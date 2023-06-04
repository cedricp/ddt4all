package org.quark.dr.ecu;

import java.util.ArrayList;

/*
 * Class to format a CAN message to single/multi line frame
 */

public class IsoTPEncode {
    private final String mmessage;
    public IsoTPEncode(String mess){
        mmessage = mess;
    }

    public String getFormatted(){
        ArrayList<String> raw_command = getFormattedArray();
        StringBuilder ret = new StringBuilder();
        for (String frame: raw_command) {
            ret.append(frame);
            ret.append("\n");
        }
        return ret.toString();
    }

    public ArrayList<String> getFormattedArray(){
        ArrayList<String> raw_command = new ArrayList<>();
        String message = mmessage;
        message = message.replace(" ", "");
        if (!IsoTPDecode.isHexadecimal(message)){
            return raw_command;
        }

        if ( (message.length() % 2) != 0 )
            return raw_command;

        int cmd_len = message.length() / 2;
        if (cmd_len < 8){
            raw_command.add(String.format("%02X", cmd_len) + message);
        } else {
            int frame_number = 1;
            String header = "1" + String.format("%03X", cmd_len);
            raw_command.add(header.substring(0,3) + message.substring(0,12));
            message = message.substring(12);
            while (message.length() > 0){
                header = "2" + String.format("%X", frame_number++);
                int remaining_len = message.length();
                raw_command.add(header + message.substring( 0, (Math.min(remaining_len, 14)) ) );
                message = message.substring( (Math.min(remaining_len, 14)) );
            }
        }

        return raw_command;
    }
}
