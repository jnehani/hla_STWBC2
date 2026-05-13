from saleae.analyzers import HighLevelAnalyzer, AnalyzerFrame, StringSetting, NumberSetting, ChoicesSetting

DISPLAY_FILTER_TYPE_CHOICES = {
    'Only known Msg Types': 'filter',
    'All Msg Types': 'all'
    }

STARTFRAME = 0x54
MOMITOR_TYPE = 0xB3
RXPACKET_TYPE = 0xC1
DATA_TYPES = [MOMITOR_TYPE, RXPACKET_TYPE]

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
        - data_frame[8]: Control error
        - data_frame[9]: Duty cycle
        - data_frame[10-11]: Bridge voltage (LSB first)
        - data_frame[12-13]: RX power (LSB first)
        - data_frame[16-17]: Input voltage (LSB first)
        """
        print("STWBC2_TYPE_MONITOR {")
        print(f"  state:          {data_frame[3]}")
        print(f"  frequency:      {data_frame[4] + data_frame[5] * 256 + data_frame[6] * 65536 + data_frame[7] * 16777216} Hz")
        print(f"  control_error:  {data_frame[8]}")
        print(f"  duty_cycle:     {data_frame[9]} %")
        print(f"  bridge_voltage: {data_frame[10] + data_frame[11] * 256} mV")
        print(f"  rx_power:       {data_frame[12] + data_frame[13] * 256} mW")
        print(f"  input_voltage:  {data_frame[16] + data_frame[17] * 256} mV")
        print("}")
        
        # Create analyzer frame with decoded information
        return AnalyzerFrame('data', msg_start, msg_end, {
            'info': f'type: Monitor, len: {data_frame[2]-3}, state: {data_frame[3]}, frequency: {data_frame[4] + data_frame[5] * 256 + data_frame[6] * 65536 + data_frame[7] * 16777216}, control_error: {data_frame[8]}, duty_cycle: {data_frame[9]}, bridge_voltage: {data_frame[10] + data_frame[11] * 256}, rx_power: {data_frame[12] + data_frame[13] * 256}, input_voltage: {data_frame[16] + data_frame[17] * 256}'
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
        payload_hex = " ".join(f"{b:02X}" for b in payload)
        print("STWBC2_TYPE_RXDATA {")
        print(f"  Rx Packet Data: {payload_hex}")
        print("}")
        
        # Create analyzer frame with decoded information
        return AnalyzerFrame('data', msg_start, msg_end, {
    'info': f"type: Rx Packet, len: {data_frame[2]-3}, RxPacket Data: {payload_hex}"
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
        if (data_frame[1] & 0x80) == 0x80:
            len = data_frame[2]-3
        else:
            len = 1
        
        print(f"unknown type: {data_frame[1]}, len: {len}, data: {str(data_frame[:])}")
        return AnalyzerFrame('data', msg_start, msg_end, {
            'info': f'type: {data_frame[1]}, len: {len}, data: {str(data_frame[:])}'
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
            if self.display_format == 'filter' and self.type not in DATA_TYPES:
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
                if self.display_format == 'all' and self.type not in DATA_TYPES:
                    response = self.unknown_type(self.byte_buffer, self.msg_start, frame.end_time)

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
