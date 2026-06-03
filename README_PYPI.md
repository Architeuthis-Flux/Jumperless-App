# Jumperless App

A Python app to control your [Jumperless](https://www.youtube.com/watch?v=fJTE7R_CV8w) breadboard, update firmware, sync with Wokwi projects, flash Arduino code, and probably some other stuff I'm forgetting right now.

Homepage: [https://jumperless.org](https://jumperless.org)

## What is Jumperless?

[Jumperless V5](https://www.crowdsupply.com/architeuthis-flux/jumperless-v5) lets you prototype like a nerdy wizard who can see electricity and conjure jumpers with a magic wand. It’s an Integrated Development Environment (IDE) for hardware, with an analog-by-nature RP2350B dev board, a drawer full of wires, and a workbench full of test equipment (including a power supply, a multimeter, an oscilloscope, a function generator, and a logic analyzer) all crammed inside a breadboard.

You can connect any point to any other using software-defined jumpers, so the four individually programmable ±8 V power supplies; ten GPIO; and seven management channels for voltage, current, and resistance can all be connected anywhere on the breadboard or the Arduino Nano header. RGB LEDs under each hole turn the breadboard itself into a display that provides real-time information about whatever’s happening in your circuit.

It's not just about being too lazy to plug in some jumpers. With software controlled wiring, the circuit itself is now [scriptable](https://jumperless-docs.readthedocs.io/en/latest/08-micropython/), which opens up a world of infinite crazy new things you could never do on a regular breadboard. Have a script try out every combination of parts until it does what you want (à la [evolvable hardware](https://evolvablehardware.org/)), automatically switch around audio effects on the fly, characterize some unknown chip with the part numbers sanded off, or don't bother with any of that and [just play Doom on it.](https://www.youtube.com/watch?v=xWYWruUO0F4)

But more likely, you'll be using it to get circuits from your brain into hardware with so little friction it feels like you're just thinking them into existence. So yeah, wizard shit.



## Installation

### Recommended: Using pipx (Automatic Virtual Environment)

The recommended way to install Jumperless is using [pipx](https://pipx.pypa.io/), which automatically creates an isolated virtual environment:

```bash
# Install pipx if you don't have it
python3 -m pip install --user pipx
python3 -m pipx ensurepath

# Install Jumperless (creates isolated venv automatically)
pipx install jumperless

# Run the application
jumperless
```

### Alternative: Using pip

You can also install with regular pip, but we recommend using a virtual environment:

```bash
# Create and activate a virtual environment
python3 -m venv jumperless-venv
source jumperless-venv/bin/activate  # On Windows: jumperless-venv\Scripts\activate

# Install Jumperless
pip install jumperless

# Run the application
jumperless
```

### Upgrading

```bash
# With pipx
pipx upgrade jumperless

# With pip
pip install --upgrade jumperless
```

## Quick Start

1. **Connect your Jumperless** device via USB
2. **Run the application**: `jumperless`
3. **Type `menu`** to see available commands
4. **Assign Wokwi projects** to slots with the `slots` command
5. **Enable automatic flashing** with the `arduino` command

## Usage

### Commands

When the application is running, you can use these commands:

- `menu`        - Open the application menu
- `slots`       - Assign Wokwi projects or local `.ino` files to slots
- `flash`       - Manually flash Arduino with assigned slot content
- `interactive` - Enable real-time character-by-character mode
- `wokwi`       - Toggle Wokwi update monitoring
- `arduino`     - Toggle Arduino auto-flashing
- `update`      - Update Jumperless firmware
- `status`      - Check connection status
- `port`        - Manually select a serial port

### Example Workflow

```bash
# Start the application
jumperless

# Assign a Wokwi project to slot 0
# Type: slots
# Enter slot number: 0
# Paste your Wokwi URL: https://wokwi.com/projects/123456789

# The app will now monitor the Wokwi project and update your Jumperless hardware
# when you make changes to the circuit
```

### Local File Monitoring

You can assign local `.ino` files to slots for automatic monitoring:

```bash
# In the slots menu, enter the path to your .ino file
/path/to/your/sketch.ino

# The app will watch this file and automatically flash your Arduino
# whenever you save changes
```

## Requirements

- Python 3.8 or higher
- Jumperless V5 (or you can just pretend you have one and load [JumperlOS](https://github.com/Architeuthis-Flux/JumperlOS/releases/latest) onto a Pico 2)

### Optional Dependencies

- Arduino CLI (automatically downloaded if needed)
- For Windows: `pywin32` and `pynput` (installed automatically)

--- 

## The Hardware

- Jocumentation: [https://jumperless.org](https://jumperless.org)
- Hardware / everything repo: [https://github.com/Architeuthis-Flux/JumperlessV5](https://github.com/Architeuthis-Flux/JumperlessV5)
- JumperlOS (the firmware): [https://github.com/Architeuthis-Flux/JumperlOS](https://github.com/Architeuthis-Flux/JumperlOS)
- Jumperless App: [https://github.com/Architeuthis-Flux/Jumperless-App](https://github.com/Architeuthis-Flux/Jumperless-App)

- Crowd Supply: [https://www.crowdsupply.com/architeuthis-flux/jumperless-v5](https://www.crowdsupply.com/architeuthis-flux/jumperless-v5)

## The Human
- Twitter: [@arabidsquid](https://x.com/arabidsquid)
- Mastodon: [leds.social/@ArchiteuthisFlux](https://leds.social/@ArchiteuthisFlux)
- Bluesky: [architeuthisflux.bsky.social](https://bsky.app/profile/architeuthisflux.bsky.social)

## Development

To contribute or run from source:

```bash
# Clone the repository
git clone https://github.com/Architeuthis-Flux/Jumperless-App.git
cd Jumperless-App

# Install in development mode
pip install -e .

# Or run directly
python JumperlessWokwiBridge.py
```


## License

This project is licensed under the GNU General Public License v3.0 or later - see the LICENSE file for details.

## Author

**Kevin Santo Cappuccio**
- Email: KevinC@ppucc.io
- GitHub: [@ArchiteuthisFlux](https://github.com/Architeuthis-Flux)

## Support

- Issues: [GitHub Issues](https://github.com/Architeuthis-Flux/JumperlessV5/issues)
- Jocumentation: [https://jumperless.org](https://jumperless.org)
- Community: [Discord](https://discord.gg/nGvT7bje7Q)

## Changelog

See [GitHub Releases](https://github.com/Architeuthis-Flux/JumperlessV5/releases) for version history and changelogs.

