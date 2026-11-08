// swift-tools-version:5.9
import PackageDescription

let package = Package(
    name: "CluCluLandRemastered",
    platforms: [.macOS(.v13)],
    products: [
        .executable(name: "CluCluLandRemastered", targets: ["CluCluLandRemastered"]),
    ],
    targets: [
        .target(
            name: "NESCore",
            path: "Sources/NESCore"
        ),
        .executableTarget(
            name: "CluCluLandRemastered",
            dependencies: ["NESCore"],
            path: "Sources/CluCluLandRemastered",
            linkerSettings: [
                .linkedFramework("Metal"),
                .linkedFramework("MetalKit"),
                .linkedFramework("AVFoundation"),
                .linkedFramework("GameController"),
            ]
        ),
    ]
)
