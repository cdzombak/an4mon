# `an4mon`: Aranet4 CO2 monitor & InfluxDB logger

`an4mon` reads from a [Aranet4 CO2 monitor](https://aranet.com/products/aranet4-home) and optionally:

- Logs the data to an InfluxDB database.
- Sends a notification via [Ntfy](https://docs.ntfy.sh/) when the CO2 level rises above a certain threshold or stays above the threshold for a certain amount of time.

## Installation

Unfortunately, as this is a Python application, some manual setup is required. You'll need a working Python installation with `virtualenv` on your system. On macOS, [I use Homebrew to manage Python](https://docs.brew.sh/Homebrew-and-Python) and install `virtualenv`.

To install this tool: clone the repository, then install the application's dependencies. The `setup-deps.sh` script creates a virtualenv and installs the requirements for you:

```shell
git clone https://github.com/cdzombak/an4mon.git
./an4mon/setup-deps.sh
```

> [!NOTE] > **Why not Docker?**
>
> I like to distribute Python applications in Docker where possible, but from my Internet searches it seems like using Bluetooth from inside a Docker container running on a macOS host is difficult or impossible.

## Usage

### Scan for Aranet devices

Working within the `an4mon` directory, run the program with the `--scan` flag to discover the address of your Aranet4 device:

```shell
./venv/bin/python ./main.py --scan
```

### Configuration

With the device's address in hand, you'll need to create a configuration JSON file. See [config.example.json](config.example.json) in this repository for an example. The configuration file is a single, valid JSON object that supports the following keys:

- `aranet_device_address`: The address of your Aranet4 device as discovered via `--scan`. Required.
- `healthcheck_ping_url`: If provided, this URL will receive a GET request after the program has successfully read from the Aranet4 device and completed notifications and/or logging to Influx.

**Notification-related keys:**

- `notify`: Whether to send notifications when CO2 reaches 'red' or 'yellow' levels.
- `ntfy_server`: The Ntfy server to use.
- `ntfy_token`: The Ntfy auth token to use. This is a string beginning with `tk_`.
- `ntfy_topic`: The Ntfy topic to send to.
- `notify_yellow_every`: Send a notification every N minutes when CO2 is in the 'yellow' range.
- `notify_red_every`: Send a notification every N minutes when CO2 is in the 'red' range.
- `notify_room_name`: The name of the room where the sensor is located, e.g. "Office".
- `ntfy_priority_yellow`: [Ntfy priority](https://docs.ntfy.sh/publish/#message-priority) for 'yellow' CO2 level notifications.
- `ntfy_priority_red`: [Ntfy priority](https://docs.ntfy.sh/publish/#message-priority) for 'red' CO2 level notifications.
- `state_file`: Path where the program will keep track of the last time it sent a notification. Required if `notify` is `true`.

**Influx-related keys:**

- `influx`: Whether to log data to InfluxDB.
- `influx_bucket`: The InfluxDB bucket to log data to. Required if `influx` is `true`.
- `influx_host`: Your InfluxDB host, e.g. `http://m-influx-on.lan`. Required if `influx` is `true`.
- `influx_port`: The InfluxDB port on `influx_host`.
- `influx_username`: InfluxDB username.
- `influx_password`: InfluxDB password.
- `influx_measurement_name`: InfluxDB measurement name. Required if `influx` is `true`.
- `influx_nametag`: Name of the room/device. If provided this is stored in the `aranet_name` tag on measurements written to InfluxDB.

### Run the program

```shell
./venv/bin/python ./main.py --config /path/to/config.json --print
```

The optional `--print` argument will print the data from the Aranet4 sensor to standard output, in addition to handling logging to Influx and notifications.

### Set up a cron or launchd job

Running the program every 2 minutes seems to result in sufficiently up-to-date data.

On macOS, do this by installing a launch agent. See [`com.dzombak.an4mon.plist`](com.dzombak.an4mon.plist) in this repository for an example. You'll need to modify the paths in that `.plist` file to match your username, `an4mon` installation, and config file path. Then, copy the `.plist` file to `~/Library/LaunchAgents/` and load it with:

```shell
launchctl load ~/Library/LaunchAgents/com.dzombak.an4mon.plist
```

On Linux, running the program every few minutes via cron is an exercise left to the reader.

## License

MIT; see [LICENSE](LICENSE) in this repository.

## Author

Chris Dzombak;

- [dzombak.com](https://www.dzombak.com/)
- [github @cdzombak](https://www.github.com/cdzombak)