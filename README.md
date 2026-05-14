# STWBC2-HB Logic Analyzer Extension

This Logic 2 High-Level Analyzer extension decodes the monitoring data from the STWBC2-HB wireless charging and power delivery chip from STMicroelectronics.

![STWBC2-HB Logic Analyzer Extension](./demo.png)

## Functionality

The analyzer decodes two message formats, both starting with the `0x54` start
marker. The format used depends on the most significant bit of the message
type byte:

- **Long messages** (`type & 0x80 == 1`): include a length byte and a variable
  payload.
  ```
  Byte 0:  0x54 (Start marker)
  Byte 1:  Message type (MSB = 1)
  Byte 2:  Payload length (N)
  Byte 3..N+2: Payload data
  ```

- **Short messages** (`type & 0x80 == 0`): no length byte; the byte right after
  the type is the single data value.
  ```
  Byte 0:  0x54 (Start marker)
  Byte 1:  Message type (MSB = 0)
  Byte 2:  Data byte
  ```

### Monitor Message (Type 0xB3)

For monitor messages (type 0xB3), the analyzer decodes and displays the following parameters:
- State: Current operating state of the chip
- Frequency: Operating frequency in Hz (4-byte value)
- Control Error: Control error value
- Duty Cycle: Current duty cycle percentage
- Bridge Voltage: Bridge voltage in mV (2-byte value)
- RX Power: Received power in mW (2-byte value)
- Input Voltage: Input voltage in mV (2-byte value)

### Rx Packet Ask message (Type 0xC1)

Decodes Rx Propetary Packet (ASK) recieved on STWBC2-HB that are send from WLC RX.
The recieved data are QI standard.

### EPT Reason (Type 0x13)

The EPT (End Power Transfer) Reason message is a short message that does not
include a length byte. It is decoded as:
- Type: `EPT Reason`
- Data: single byte containing the reason code (displayed in hex, e.g. `0x07`)

Message structure:
```
Byte 0:  0x54 (Start marker)
Byte 1:  0x13 (Message type - EPT Reason)
Byte 2:  Reason code (1 byte)
```

### System Event (Type 0x22)

The System Event message is a short message (no length byte) used by the
STWBC2-HB to report internal state changes, errors and timeouts. The
analyzer decodes the event code into a human-readable name. It is decoded
as:
- Type: `System Event`
- Data: event name string (e.g. `AFE_INIT_DONE`, `EPT_CHARGE_COMPLETE`,
  `PING_TIMEOUT`, ...). If the event code is not recognized, it is shown as
  `UNKNOWN_EVENT_0xNN`.

Message structure:
```
Byte 0:  0x54 (Start marker)
Byte 1:  0x22 (Message type - System Event)
Byte 2:  Event code (1 byte)
```

Recognized event codes include (non-exhaustive):

| Code  | Name                              |
|-------|-----------------------------------|
| 0x01  | AFE_INIT_DONE                     |
| 0x02  | CHARGING_AT_REDUCED_RATE          |
| 0x03  | BAD_NEGOTIATION                   |
| 0x04  | QFOD                              |
| 0x06  | ENTER_NEGOTIATION                 |
| 0x0B  | EPT_CHARGE_COMPLETE               |
| 0x0C  | EPT_OVER_VOLTAGE                  |
| 0x10  | EPT_NO_RESPONSE                   |
| 0x16  | ENTER_POWER_TRANSFER              |
| 0x1A  | ENTER_CALIBRATION                 |
| 0x20  | OBJECT_REMOVED                    |
| 0x2D  | CHIP_OVERTEMP_DETECTED            |
| 0xF0  | PING_TIMEOUT                      |
| 0xF3  | PACKET_TIMEOUT                    |
| 0xF4  | NEGOTIATION_TIMEOUT               |

See the `SYS_EVENT` dictionary in `HighLevelAnalyzer.py` for the full list.

### Unknown Short Messages

Some message types do not carry a length byte (i.e. their type byte has the
MSB cleared, `type & 0x80 == 0`). For these, the analyzer treats the next byte
as the data value and emits a short frame containing:
- Type: hex representation of the message type byte (e.g. `0x42`)
- Data: single data byte in hex (e.g. `0x0A`)

These short messages are only shown when the `Display Types` setting is set
to `All Msg Types`. With `Only known Msg Types`, only `EPT Reason` and
`System Event` short messages are displayed.

### Other Unknown Messages

For other message types, the analyzer displays:
- Message type
- Message length
- Raw data bytes

## Usage

1. Install this extension in Logic 2
2. Add it as an analyzer to your capture
3. Configure it to analyze your STWBC2-HB communication channel
4. The decoded messages will be displayed in the Logic 2 interface

## Message Format Details

### Monitor Message Structure (0xB3)
```
Byte 0:  0x54 (Start marker)
Byte 1:  0xB3 (Message type)
Byte 2:  Length
Byte 3:  State
Bytes 4-7: Frequency (LSB first)
Byte 8:  Control Error
Byte 9:  Duty Cycle
Bytes 10-11: Bridge Voltage (LSB first)
Bytes 12-13: RX Power (LSB first)
Bytes 16-17: Input Voltage (LSB first)
```

###  Rx Propetary Packet Message Structure (0xC1)
```
Byte 0:  0x54 (Start marker)
Byte 1:  0xC1 (Message type)
Byte 2:  Length
Byte 3:Length  Bytes Recieved based on QI protocol
```

### EPT Reason / Short Message Structure
Short messages (type byte with MSB = 0) have no length field:
```
Byte 0:  0x54 (Start marker)
Byte 1:  Message type (e.g. 0x13 for EPT Reason)
Byte 2:  Data byte (e.g. EPT reason code)
```