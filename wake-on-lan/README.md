# Wake-on-LAN

Send a Wake-on-LAN magic packet from a tiny Python script.

## Run

```bash
uv run python wake-on-lan/wol.py
```

## Edit

Set these at the top of `wol.py`:

- `TARGET_IP = "192.168.1.137"`
- `TARGET_MAC = "aa:bb:cc:dd:ee:ff"` if you know it

## Notes

- Uses only the Python standard library
- WOL packets target a MAC address; the IP is used here to derive the local broadcast address
- On Linux, the script will try `/proc/net/arp` first if `TARGET_MAC` is left unset
