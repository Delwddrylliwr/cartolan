# Cartolan - Trade Winds

This project aims to provide various support to the development of the board game [Cartolan - Trade Winds](https://docs.google.com/document/d/1LuAe_V7xUiPdksBD5XowbvPdK9tO_SFwECsiqNrPXLY/edit)

It simulates large numbers of games beyond what could be expected from human playtesters, albeit with virtual players using simple heuristics (and in future deep Q-learning). 

It also allows playtesting through virtual play over a network and the internet, through a browser or mobile device.

## Getting Started

All the scripts are in the root folder, while assets like visuals are in subfolders. 

The key file through which to run simulations is main_sim.py.

The key files for hosting a web app are web_app.py and cartolan_web/public_html/http_server.py.

See deployment for notes on how to deploy the project on a live system.

### Prerequisites

For simulation with stats and visuals, you will need the Matplotlib and Tkinter python packages. The first is available through pip, but the latter has to be [installed independently](https://tkdocs.com/tutorial/install.html)

For serving the web application, you will need pygame and SimpleWebSocketServer, both available through pip.

## Configuring the game

Various aspects of the rules can be configured based on constants in game_config.py .

## Running the tests

Automated tests have not been implemented yet. Testing can be done through comparing virtual play to the rules explained in the game manual.

## Deployment

Simulations of the game can be run using the Jupyter notebook from the root directory.

Internet play of the game will require an accessible server to have both the web_app.py and cartolan_web/public_html/http_server.py servers to be running. If this server has an IP address of x.y.z.w, then by default a desktop or mobile web browser can play the game by loading:

```
x.y.z.w:9000/index.html
```
**But, at present, the IP address is hard coded into the files.**

## Built With

Python 3.8, tested on Python 3.6

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
