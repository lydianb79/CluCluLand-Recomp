import Foundation
import AVFoundation

/// Pulls samples from the emulator's lock-free ring buffer on the audio render thread.
final class AudioOutput {
    private let engine = AVAudioEngine()
    private var source: AVAudioSourceNode?
    private(set) var sampleRate: Double = 48000
    private var configObserver: NSObjectProtocol?

    init(pull: @escaping (UnsafeMutablePointer<Float>, Int) -> Int) {
        let hwFormat = engine.outputNode.outputFormat(forBus: 0)
        sampleRate = hwFormat.sampleRate > 8000 ? hwFormat.sampleRate : 48000
        guard let format = AVAudioFormat(standardFormatWithSampleRate: sampleRate, channels: 1) else { return }

        // boxed so the (possibly @Sendable) render block never mutates a captured `var`
        final class FadeState { var last: Float = 0 }
        let fade = FadeState()
        let node = AVAudioSourceNode(format: format) { _, _, frameCount, audioBufferList -> OSStatus in
            var last = fade.last
            defer { fade.last = last }
            let buffers = UnsafeMutableAudioBufferListPointer(audioBufferList)
            guard buffers.count > 0, let mData = buffers[0].mData else { return noErr }
            let out = mData.assumingMemoryBound(to: Float.self)
            let n = Int(frameCount)
            let got = pull(out, n)
            if got > 0 { last = out[got - 1] }
            if got < n {
                // underrun: fade the last sample out instead of clicking
                for i in got..<n { last *= 0.995; out[i] = last }
            }
            if buffers.count > 1 {
                for b in 1..<buffers.count {
                    if let d = buffers[b].mData { memcpy(d, mData, n * MemoryLayout<Float>.size) }
                }
            }
            return noErr
        }
        source = node
        engine.attach(node)
        engine.connect(node, to: engine.mainMixerNode, format: format)
        engine.prepare()
        do { try engine.start() } catch { NSLog("Audio engine failed to start: \(error)") }

        configObserver = NotificationCenter.default.addObserver(
            forName: .AVAudioEngineConfigurationChange, object: engine, queue: .main
        ) { [weak self] _ in
            guard let self else { return }
            if !self.engine.isRunning { try? self.engine.start() }
        }
    }

    deinit {
        if let configObserver { NotificationCenter.default.removeObserver(configObserver) }
        engine.stop()
    }

    func setVolume(_ v: Float) {
        engine.mainMixerNode.outputVolume = max(0, min(1, v))
    }
}
