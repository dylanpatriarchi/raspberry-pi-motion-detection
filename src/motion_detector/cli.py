"""
Command Line Interface
Entry point and argument parsing for the motion detection system.
"""

import argparse
import sys

from . import __version__
from .core.detector import MotionDetector
from .utils.validators import run_system_diagnostics
from .utils.logger import setup_logger


def create_argument_parser() -> argparse.ArgumentParser:
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        prog="motion-detector",
        description="Professional Motion Detection System for Raspberry Pi",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Run with default settings
  %(prog)s --config custom.json     # Use custom configuration
  %(prog)s --debug                  # Enable debug mode
  %(prog)s --no-preview             # Disable preview window
  %(prog)s --diagnostics            # Run system diagnostics only

Interactive Controls (when preview is enabled):
  q - Quit application
  r - Reset background frame
  s - Save manual photo
        """,
    )

    parser.add_argument(
        "--config",
        "-c",
        type=str,
        help="Path to configuration file (default: config/settings.json)",
    )

    parser.add_argument(
        "--debug", "-d", action="store_true", help="Enable debug mode with verbose logging"
    )

    parser.add_argument(
        "--no-preview",
        action="store_true",
        help="Disable preview window (useful for headless operation)",
    )

    parser.add_argument(
        "--diagnostics", action="store_true", help="Run system diagnostics and exit"
    )

    parser.add_argument("--version", "-v", action="version", version=f"%(prog)s {__version__}")

    return parser


def run_diagnostics() -> bool:
    """Run system diagnostics and display results.

    Returns:
        bool: True if the system is ready, False otherwise.
    """
    print("🔍 Running System Diagnostics...")
    print("=" * 50)

    logger = setup_logger("Diagnostics", level="INFO")
    results = run_system_diagnostics(logger)

    print("\n📊 System Information:")
    sys_info = results.get("system_info", {})
    print(f"  Platform: {sys_info.get('platform', 'Unknown')}")
    print(f"  Architecture: {sys_info.get('machine', 'Unknown')}")
    print(f"  Python Version: {sys_info.get('python_version', 'Unknown')}")
    print(f"  CPU Cores: {sys_info.get('cpu_count', 'Unknown')}")
    print(f"  Memory: {sys_info.get('memory_gb', 0):.1f} GB")

    print("\n🔧 Component Status:")
    print(f"  OpenCV: {'✅ Available' if results.get('opencv_available') else '❌ Not Available'}")
    if results.get("opencv_version"):
        print(f"    Version: {results['opencv_version']}")

    print(
        f"  Camera: {'✅ Accessible' if results.get('camera_accessible') else '❌ Not Accessible'}"
    )
    if results.get("camera_message"):
        print(f"    {results['camera_message']}")

    print(f"  Disk Space: {'✅ OK' if results.get('disk_space_ok') else '⚠️  Low'}")
    if results.get("disk_free_gb"):
        print(f"    Available: {results['disk_free_gb']:.1f} GB")

    print(f"  Memory: {'✅ OK' if results.get('memory_ok') else '⚠️  Low'}")
    if results.get("memory_available_mb"):
        print(f"    Available: {results['memory_available_mb']:.0f} MB")

    print(f"\n🎯 System Ready: {'✅ YES' if results.get('system_ready') else '❌ NO'}")

    if not results.get("system_ready"):
        print("\n💡 Recommendations:")
        print("  - Install missing dependencies: pip install -r requirements.txt")
        print("  - Check camera connection and permissions")
        print("  - Ensure sufficient disk space and memory")
        print("  - On Raspberry Pi, enable camera: sudo raspi-config")

        return False

    return True


def main() -> None:
    """Main entry point."""
    parser = create_argument_parser()
    args = parser.parse_args()

    # Show banner
    print("🎥 Raspberry Pi Motion Detection System")
    print(f"   Professional Edition v{__version__}")
    print("=" * 50)

    # Run diagnostics if requested
    if args.diagnostics:
        success = run_diagnostics()
        sys.exit(0 if success else 1)

    try:
        # Create motion detector instance
        detector = MotionDetector(config_file=args.config)

        # Apply command line overrides
        if args.debug:
            detector.settings.logging.level = "DEBUG"
            detector.settings.system.debug_mode = True
            print("🐛 Debug mode enabled")

        if args.no_preview:
            detector.settings.display.show_preview = False
            print("📺 Preview disabled")

        # Display configuration summary
        camera_cfg = detector.settings.camera
        print("\n⚙️  Configuration Summary:")
        print(f"  Camera: {camera_cfg.resolution} @ {camera_cfg.framerate}fps")
        print(f"  Motion Threshold: {detector.settings.detection.motion_threshold}")
        print(f"  Output Directory: {detector.settings.storage.output_directory}")
        print(f"  Photo Delay: {detector.settings.storage.photo_delay}s")
        print(f"  Preview: {'Enabled' if detector.settings.display.show_preview else 'Disabled'}")
        print(f"  Debug Mode: {'Enabled' if detector.settings.system.debug_mode else 'Disabled'}")

        # Quick system check
        print("\n🔍 Quick System Check...")
        if detector.settings.system.debug_mode:
            run_diagnostics()

        print("\n🚀 Starting Motion Detection System...")
        print("   Press Ctrl+C to stop")

        if detector.settings.display.show_preview:
            print("   Interactive controls:")
            print("     q - Quit")
            print("     r - Reset background")
            print("     s - Save photo")

        # Start the system
        with detector:
            detector.start()

    except KeyboardInterrupt:
        print("\n👋 Shutting down gracefully...")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if args.debug:
            import traceback

            traceback.print_exc()
        sys.exit(1)

    print("✅ Motion Detection System stopped")


if __name__ == "__main__":
    main()
