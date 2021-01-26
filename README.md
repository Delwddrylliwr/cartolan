# Cartolan - Trade Winds

This project aims to provide various support to the development of the board game [Cartolan - Trade Winds](https://docs.google.com/document/d/1LuAe_V7xUiPdksBD5XowbvPdK9tO_SFwECsiqNrPXLY/edit)

It simulates large numbers of games beyond what could be expected from human playtesters, albeit with virtual players using simple heuristics (and in future deep Q-learning). 

It also allows playtesting through virtual play over a network and the internet.

## Getting Started

All the scripts are in the root folder, while assets like visuals are in subfolders. 

The key file through which to run simulations is cartolan_sim.py.

The key file through which to play the game is cartolan_game.py.

See deployment for notes on how to deploy the project on a live system.

### Prerequisites

For simulation with stats and visuals, you will need the Matplotlib and Tkinter python packages. The first is available through pip, but the latter has to be [installed independently](https://tkdocs.com/tutorial/install.html)

For virtual play of the game, you will need the pygame and podsixnet python packages. Both are available through pip, but not in many distributions like Anaconda:

If your python 3.x instance is called with the command ```python3``` then you'll need to install these with:
```
python3 -m pip install pygame
```

### Installing

To achieve a convenient installation, the pyinstaller package can be used to convert the python source files into an executable for whichever operating system it is run on:

The package can be installed through:
```
python3 -m pip install pyinstaller
```
It can then be used to create a simple executable (in the "dist" subfolder of the project) through running this command in the project root folder:
```
pyinstaller --onefile cartolan_game.py
```

End with an example of getting some data out of the system or using it for a little demo

## Configuring the game

Various aspects of the rules can be configured based on constants in game_config.py .

## Running the tests

Automated tests have not been implemented yet. Testing can be done through comparing virtual play to the rules explained in the game manual.

## Deployment

Simulations of the game can be run using the Jupyter notebook from the root directory.

Virtual play of the game over a network will need the server.py script to be run first, and a valid IP address specified, before the game executable is run, choosing "network" mode and then giving the same IP.

## Built With

Python 3.8

## Contributing

If you'd like to contribute to this project then please contact Tom Wilkinson @ delwddrylliwr@gmail.com

## Versioning

Git and GitHub are used for versioning. 

## Authors

* **Tom Wilkinson** - *Creator of the Cartolan board game, and developer of this project.* 

## License

This project is licensed under the CC-BY-NC, Creative Commons Attribution Non-Commercial license.

## Acknowledgments

* Thanks to the [podsixnet tutorial](https://www.raywenderlich.com/2613-multiplayer-game-programming-for-teens-with-python-part-2) of Julian Meyer.
* Thanks to the [deep Q-learning tutorial](https://keras.io/examples/rl/deep_q_network_breakout/) of Jacob Chapman and Mathias Lechner
