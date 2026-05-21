from saleae.analyzers import HighLevelAnalyzer, AnalyzerFrame, StringSetting, NumberSetting, ChoicesSetting

DISPLAY_FILTER_TYPE_CHOICES = {
    'Only known Msg Types': 'filter',
    'All Msg Types': 'all'
    }


SYS_EVENT = {
    0x01: "AFE_INIT_DONE",
    0x02: "CHARGING_AT_REDUCED_RATE",
    0x03: "BAD_NEGOTIATION",
    0x04: "QFOD",
    0x05: "BAD_PACKET_SEQUENCE",
    0x06: "ENTER_NEGOTIATION",
    0x07: "OPTIONAL_PACKETS_MISMATCH",
    0x08: "POWER_CTRL_HOLD_OFF_ERROR",
    0x09: "TOO_MANY_PROPRIETARY_PACKETS",
    0x0A: "WRONG_RP_FORMAT",
    0x0B: "EPT_CHARGE_COMPLETE",
    0x0C: "EPT_OVER_VOLTAGE",
    0x0D: "EPT_RX_OVER_CURRENT",
    0x0E: "EPT_RX_OVER_TEMPERATURE",
    0x0F: "EPT_BATTERY_FAILURE",
    0x10: "EPT_NO_RESPONSE",
    0x12: "EPT_NEGOTIATION_FAILURE",
    0x13: "EPT_RESTART_POWER_TRANSFER",
    0x14: "EPT_UNKNOWN",
    0x15: "EPT_RECEIVED",
    0x16: "ENTER_POWER_TRANSFER",
    0x17: "BAD_MODE_VALUE_IN_MP_RP_PACKET",
    0x18: "BAD_PACKET_RECEIVED",
    0x19: "HANDLER_ERROR",
    0x1A: "ENTER_CALIBRATION",
    0x1B: "CHARGING_AT_FAST_RATE",
    0x1C: "PRES_DET_CAL_DONE",
    0x1D: "QFACTOR_CAL_DONE",
    0x1E: "FOD_DURING_POWER",
    0x1F: "BPP_QFOD",
    0x20: "OBJECT_REMOVED",
    0x21: "ENTER_POWER_LIMITATION",
    0x22: "LEAVE_POWER_LIMITATION",
    0x23: "ENTER_CURRENT_LIMITER",
    0x24: "LEAVE_CURRENT_LIMITER",
    0x25: "OVERLOAD_DETECTED",
    0x26: "SCHEDULER_MSG_ERROR",
    0x27: "SCHEDULER_TIMER_ERROR",
    0x28: "SENSING_MUX_ERROR",
    0x29: "NTC_OVERTEMP_DETECTED",
    0x2A: "FOD_DURING_NEGOTIATION",
    0x2B: "PWR_SRC_ERROR",
    0x2C: "FSK_PKT_ERROR",
    0x2D: "CHIP_OVERTEMP_DETECTED",
    0x2E: "AFE_INT_ERROR",
    0x2F: "ADC_CAL_DONE",
    0x30: "RESTART_FOR_CAL",
    0x31: "ENTER_RING_V_LIMITER",
    0x32: "LEAVE_RING_V_LIMITER",
    0x40: "EPT_REPING",
    0x41: "ENTER_POWER_TRANSFER_AT_STSC",
    0x42: "RESTART_FOR_OVER_VOLTAGE",
    0xF0: "PING_TIMEOUT",
    0xF1: "T_FIRST_TIMEOUT",
    0xF2: "NEXT_PACKET_TIMEOUT",
    0xF3: "PACKET_TIMEOUT",
    0xF4: "NEGOTIATION_TIMEOUT",
    0xF5: "CONTROL_ERROR_TIMEOUT",
    0xF6: "RECEIVED_POWER_TIMEOUT",
    0xF7: "CALIBRATION_PHASE_TOO_LONG",
}

STARTFRAME = 0x54
MOMITOR_TYPE = 0xB3
RXPACKET_TYPE = 0xC1
EPT_REASON_TYPE = 0x13
SYS_EVENT_TYPE = 0x22
DATA_TYPES = [MOMITOR_TYPE, RXPACKET_TYPE]
DATA_SHORT_TYPES = [EPT_REASON_TYPE, SYS_EVENT_TYPE]

class Hla(HighLevelAnalyzer):
    """
    High Level Analyzer for STWBC2-HB wireless charging and power delivery chip.
    Decodes monitoring messages and other communication data from the chip.
    """

    # State variables for message processing
    msg_start = None      # Timestamp of message start
    byte_buffer = []      # Buffer to collect message bytes
    expected_len = 0      # Expected total message length
    frames = []          # Collection of processed frames
    
    # Settings (for future use)
    my_string_setting = StringSetting()
    my_number_setting = NumberSetting(min_value=0, max_value=100)
    display_types_setting = ChoicesSetting(label='Display Types', choices=DISPLAY_FILTER_TYPE_CHOICES.keys())

    # Define how the decoded data should be displayed in Logic 2
    result_types = {
        'data': {
            'format': '{{data.info}}'  # Display format for decoded messages
        }
    }

    def __init__(self):
        """Initialize the analyzer and print current settings"""
        self.display_format = DISPLAY_FILTER_TYPE_CHOICES.get(self.display_types_setting, 'filter')

    def monitor_type(self, data_frame: AnalyzerFrame, msg_start: int, msg_end: int):
        """
        Process monitor message type (0xB3)
        Decodes operational parameters from the STWBC2-HB chip

        Parameters:
        - data_frame: List of bytes containing the message data
        - msg_start: Start timestamp of the message
        - msg_end: End timestamp of the message

        Message structure:
        - data_frame[0]: Start marker (0x54)
        - data_frame[1]: Message type (0xB3)
        - data_frame[2]: Message length
        - data_frame[3]: Chip state
        - data_frame[4-7]: Frequency (LSB first)
        - data_frame[8]: Control error (positive or negative value))
        - data_frame[9]: Duty cycle
        - data_frame[10-11]: Bridge voltage (LSB first)
        - data_frame[12-15]: RX power (LSB first)
        - data_frame[16-17]: Input voltage (LSB first)
        - data_frame[18]: Coil Temperature
        - data_frame[19-20]: Coil Current (LSB first)
        - data_frame[25-26]: Fod Margin
        - data_frame[27]:  Bridge Mode
        """
        control_error = data_frame[8] - 256 if data_frame[8] >= 128 else data_frame[8]
        fod_margin_raw = data_frame[25] + data_frame[26] * 256
        fod_margin = fod_margin_raw - 65536 if fod_margin_raw >= 32768 else fod_margin_raw
        print("STWBC2_TYPE_MONITOR {")
        print(f"  state:          {data_frame[3]}")
        print(f"  frequency:      {data_frame[4] + data_frame[5] * 256 + data_frame[6] * 65536 + data_frame[7] * 16777216} Hz")
        print(f"  control_error:  {control_error}")
        print(f"  duty_cycle:     {data_frame[9]} %")
        print(f"  bridge_voltage: {data_frame[10] + data_frame[11] * 256} mV")
        print(f"  rx_power:       {data_frame[12] + data_frame[13] * 256 + data_frame[14] * 65536 + data_frame[15] * 16777216} mW")
        print(f"  input_voltage:  {data_frame[16] + data_frame[17] * 256} mV")
        print(f"  coil_temperature: {data_frame[18]} °C")
        print(f"  coil_current:   {data_frame[19] + data_frame[20] * 256} mA")
        print(f"  fod_margin:     {fod_margin} mW")
        print(f"  bridge_mode:    {data_frame[27]}")
        print("}")
        
        # Create analyzer frame with decoded information
        return AnalyzerFrame('data', msg_start, msg_end, {
            'info': f'type: Monitor, len: {data_frame[2]-3}, state: {data_frame[3]}, frequency: {data_frame[4] + data_frame[5] * 256 + data_frame[6] * 65536 + data_frame[7] * 16777216}, control_error: {control_error}, duty_cycle: {data_frame[9]}, bridge_voltage: {data_frame[10] + data_frame[11] * 256}, rx_power: {data_frame[12] + data_frame[13] * 256 + data_frame[14] * 65536 + data_frame[15] * 16777216}, input_voltage: {data_frame[16] + data_frame[17] * 256}, coil_temperature: {data_frame[18]}, coil_current: {data_frame[19] + data_frame[20] * 256}, fod_margin: {fod_margin}, bridge_mode: {data_frame[27]}'

        })

    def RxPacket_type(self, data_frame: AnalyzerFrame, msg_start: int, msg_end: int):
        """
        Process Rx Packet Ask message type (0xC1)
        Decodes Rx Propetary Packet recieved on STWBC2-HB chip

        Parameters:
        - data_frame: List of bytes containing the message data
        - msg_start: Start timestamp of the message
        - msg_end: End timestamp of the message

        Message structure:
        - data_frame[0]: Start marker (0x54)
        - data_frame[1]: Message type (0xC1)
        - data_frame[2]: Message length
        - data_frame[3:]: Message
        """
        length = data_frame[2]
        payload = data_frame[3:3 + length]
        payload_hex = " ".join(f"0x{b:02X}" for b in payload)
        print("STWBC2_TYPE_RXDATA {")
        print(f"  Rx Packet Data: {payload_hex}")
        print("}")
        
        # Create analyzer frame with decoded information
        return AnalyzerFrame('data', msg_start, msg_end, {'info': f"type: Rx Packet, len: {length}, RxPacket Data: {payload_hex}"})


    def short_type(self, data_frame: AnalyzerFrame, msg_start: int, msg_end: int):
        """
        Process short message types (messages without a length byte).
        Message structure:
        - data_frame[0]: Start marker (0x54)
        - data_frame[1]: Message type
        - data_frame[2]: Data byte (value)

        Currently handles:
        - EPT_REASON_TYPE (0x13): End Power Transfer reason
        """
        msg_type = data_frame[1]
        value = data_frame[2]

        if msg_type == EPT_REASON_TYPE:
            type_name = "EPT Reason"
            data_str = f"0x{value:02X}"
        elif msg_type == SYS_EVENT_TYPE:
            type_name = "System Event"
            data_str = SYS_EVENT.get(value, f"UNKNOWN_EVENT_0x{value:02X}")
        else:
            type_name = f"0x{msg_type:02X}"
            data_str = f"0x{value:02X}"

        print("STWBC2_TYPE_SHORT {")
        print(f"  type: {type_name}")
        print(f"  data: {data_str}")
        print("}")

        return AnalyzerFrame('data', msg_start, msg_end, {
            'info': f'type: {type_name}, data: {data_str}'
        })

    def unknown_type(self, data_frame: AnalyzerFrame, msg_start: int, msg_end: int):
        """
        Process unknown message types
        Displays raw message data for debugging or future implementation

        Parameters:
        - data_frame: List of bytes containing the message data
        - msg_start: Start timestamp of the message
        - msg_end: End timestamp of the message
        """
        
        len = data_frame[2]
        data_hex = " ".join(f"0x{b:02X}" for b in data_frame[3:])

        print(f"unknown type: 0x{data_frame[1]:02X}, len: {len}, data: {data_hex}")
        return AnalyzerFrame('data', msg_start, msg_end, {
            'info': f'type: 0x{data_frame[1]:02X}, len: {len}, data: {data_hex}'
        })
    
    def decode(self, frame: AnalyzerFrame):
        """
        Main decode function that processes each incoming byte
        Implements a state machine to collect and process message bytes

        Message format:
        1. Start marker (0x54)
        2. Message type
        3. Message length
        4. Message data (length specified in byte 3)
        """
        # Extract the data byte from the frame
        data = frame.data['data'][0]

        # State machine for message processing
        if len(self.byte_buffer) == 0 and data == STARTFRAME:
            # New message detected (0x54)
            self.byte_buffer = []
            self.msg_start = frame.start_time
            self.byte_buffer.append(data)

        elif len(self.byte_buffer) == 1:
            # Second byte is message type
            self.type = data
            if self.display_format == 'filter' and self.type not in DATA_TYPES and self.type not in DATA_SHORT_TYPES:
                # Skip unknown types if filter is enabled
                self.byte_buffer = []
                self.msg_start = None
                return None
            else:
                self.byte_buffer.append(data)

        elif len(self.byte_buffer) == 2: 
            self.byte_buffer.append(data)          
            if (self.type & 0x80) == 0x80:
                # If there is the lenght, add 3 to include start marker, type, and length bytes
                self.expected_len = data + 3
            else:
                # There are some data that does not contain length, and the data are as 0x54 <type> <value>.
                # In this case, we should display the latest message and restart the frame from this byte.
                self.expected_len = 3
                response = None
                # Call short_type when:
                #   - the type is a known short type, OR
                #   - display_format is 'all' (show everything, including unknown short types)
                # When display_format is 'filter' and the type is not in DATA_SHORT_TYPES, skip it.
                if self.type in DATA_SHORT_TYPES or self.display_format == 'all':
                    response = self.short_type(self.byte_buffer, self.msg_start, frame.end_time)
                # Reset for next message
                self.byte_buffer = []
                self.msg_start = None
                return response

        elif len(self.byte_buffer) > 0 and len(self.byte_buffer) < self.expected_len:
            # Collect message data bytes
            self.byte_buffer.append(data)
            
        # Check if we have a complete message
        if len(self.byte_buffer) > 0 and len(self.byte_buffer) == self.expected_len:
            response = None

            # Process based on message type
            if self.type == MOMITOR_TYPE:
                # Monitor message type
                response = self.monitor_type(self.byte_buffer, self.msg_start, frame.end_time)
            elif self.type == RXPACKET_TYPE:
                # RxPAcket message type
                response = self.RxPacket_type(self.byte_buffer, self.msg_start, frame.end_time)
            else:
                if self.display_format == 'all':
                    # Unknown message type
                    response = self.unknown_type(self.byte_buffer, self.msg_start, frame.end_time)
            
            # Reset for next message
            self.byte_buffer = []
            self.msg_start = None
            return response
            
        return None
