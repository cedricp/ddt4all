package org.quark.dr.ecu;

import android.util.Log;
import android.util.Pair;
import org.json.JSONArray;
import org.json.JSONObject;
import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.math.BigInteger;
import java.text.DecimalFormat;
import java.text.DecimalFormatSymbols;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Iterator;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;

public class Ecu {
    public String global_endian;
    private HashMap<String, EcuRequest> requests;
    private HashMap<String, EcuData> data;
    private HashMap<String, String> sdsrequests;
    private String protocol;
    private String funcaddr;
    private String ecu_name;
    private String kw1, kw2, ecu_send_id, ecu_recv_id;
    private boolean fastinit;
    private String m_defaultSDS;

    private class EcuDataItem{
        public int firstbyte;
        public int bitoffset;
        public boolean ref;
        public String endian = "";
        public String req_endian;
        public String name;
        EcuDataItem(JSONObject json, String name){
            req_endian = global_endian;
            this.name = name;
            try {
                if (json.has("firstbyte")) firstbyte = json.getInt("firstbyte");
                if (json.has("bitoffset")) bitoffset = json.getInt("bitoffset");
                if (json.has("ref")) ref = json.getBoolean("ref");
                if (json.has("endian")) endian = json.getString("endian");
            } catch (Exception e){
                e.printStackTrace();
            }
        }
    }

    public HashMap<String, String> getSdsrequests(){
        return sdsrequests;
    }

    public void setDefautSDS(String sdsname){
        if (sdsrequests.containsKey(sdsname))
            m_defaultSDS = sdsrequests.get(sdsname);
    }

    private static class EcuDevice {
        public int dtc;
        public int dtctype;
        HashMap<String, String> devicedata;
        public String name;

        EcuDevice(JSONObject json){
            devicedata = new HashMap<>();
            try {
                this.name = json.getString("name");
                dtctype = json.getInt("dtctype");
                dtc = json.getInt("dtc");

                JSONObject devdataobj = json.getJSONObject("devicedata");
                Iterator<String> keys = devdataobj.keys();
                while (keys.hasNext()) {
                    String key = keys.next();
                    devicedata.put(key, devdataobj.getString(key));
                }
            } catch (Exception e){

            }
        }
    }

    public class EcuData {
        public int bitscount = 8;
        public boolean scaled = false;
        public boolean signed = false;
        public boolean isbyte = false;
        public boolean binary = false;
        public int bytescount = 1;
        public boolean bytesascii = false;
        public float step = 1.0f;
        public float offset = 0.0f;
        public float divideby = 1.0f;
        public String format = "";
        public HashMap<Integer, String> lists;
        public HashMap<String, Integer> items;
        public String description;
        public String unit = "";
        public String comment = "";
        public String name;
        EcuData(JSONObject json, String name) {
            this.name = name;
            try {
                lists = new HashMap<>();
                items = new HashMap<>();
                if(json.has("bitscount"))
                    bitscount = json.getInt("bitscount");

                if(json.has("scaled"))
                    scaled = json.getBoolean("scaled");

                if(json.has("byte"))
                    isbyte = json.getBoolean("byte");

                if(json.has("signed"))
                    signed = json.getBoolean("signed");
                if(json.has("binary"))

                    binary = json.getBoolean("binary");
                if(json.has("bytesascii"))
                    bytesascii = json.getBoolean("bytesascii");

                if(json.has("bytescount"))
                    bytescount = json.getInt("bytescount");

                if(json.has("step"))
                    step = (float)json.getDouble("step");

                if(json.has("offset"))
                    offset = (float)json.getDouble("offset");

                if(json.has("divideby"))
                    divideby = (float)json.getDouble("divideby");

                if(json.has("format"))
                    format = json.getString("format");

                if(json.has("description"))
                    description = json.getString("description");

                if(json.has("unit"))
                    unit = json.getString("unit");

                if(json.has("comment"))
                    comment = json.getString("comment");

                if (json.has("lists")) {
                    JSONObject listobj = json.getJSONObject("lists");
                    Iterator<String> keys = listobj.keys();
                    while (keys.hasNext()) {
                        String key = keys.next();
                        lists.put(Integer.parseInt(key), listobj.getString(key));
                        items.put(listobj.getString(key), Integer.parseInt(key));
                    }
                }
            } catch (Exception e) {
                e.printStackTrace();
            }
        }

        public byte[] setValue(Object value, byte[] byte_list, EcuDataItem dataitem){
            int start_byte = dataitem.firstbyte - 1;
            int startBit = dataitem.bitoffset;
            boolean little_endian = false;

            int requiredDataBytesLen = (int)(Math.ceil(((float)bitscount + (float)startBit) / 8.0f));

            if (global_endian.equals("Little"))
                little_endian = true;

            if (dataitem.endian.equals("Little"))
                little_endian = true;

            if (dataitem.endian.equals("Big"))
                little_endian = false;


            /*
             * Not sure it's required to format little endian values...
             * Will have to check that
             */
            little_endian = false;

            String finalbinvalue;

            if (bytesascii){
                if (!(value instanceof String)){
                    throw new ClassCastException("Value must be a string");
                }
                String strvalue = (String)value;
                if (bytescount > strvalue.length())
                    strvalue = padLeft(strvalue, bytescount, " ");
                if (bytescount < strvalue.length())
                    strvalue = strvalue.substring(0, bytescount);

                strvalue = stringToHex(strvalue);
                finalbinvalue = hexToBinary(strvalue);
            } else {
                if (scaled) {
                    // We want a float or integer here
                    float floatval;
                    if (value instanceof Integer) {
                        floatval = (float) ((Integer) value);
                    } else if (value instanceof Float) {
                        floatval = (float) value;
                    } else if (value instanceof String) {
                        // Replace comma with point and remove spaces
                        value = ((String) value).replace(",", ".");
                        value = ((String) value).replace(" ", "");
                        floatval = Float.parseFloat((String)value);
                    } else {
                        throw new ClassCastException("Value must be an integer or float");
                    }


                    floatval = ((floatval * divideby) - offset) / step;
                    int intval = (int) floatval;
                    finalbinvalue = integerToBinaryString(intval, bitscount);
                } else {
                    // Hex string
                    if (!(value instanceof String)) {
                        throw new ClassCastException("Value must be a hex string");
                    }
                    String vv = (String)value;
                    finalbinvalue = hexToBinary(vv.replaceAll(" ", ""));
                }
            }

            finalbinvalue = padLeft(finalbinvalue, bitscount, "0");
            int numreqbytes = (int)(Math.ceil(((float)(bitscount + startBit) / 8.f)));

            byte[] request_bytes = Arrays.copyOfRange(byte_list, start_byte, start_byte + numreqbytes);
            StringBuilder requestasbin = new StringBuilder();
            String bitmask = padLeft("", bitscount, "1");

            for (byte request_byte : request_bytes) {
                requestasbin.append(byteToBinaryString(request_byte, 8));
            }

            if (little_endian){
                /*
                 * Handle little endian value (not an easy task...)
                 */
                // Moves the bytes to to left
                for (int i = 0; i < startBit; ++i) {
                    finalbinvalue += "0";
                    bitmask += "0";
                }

                finalbinvalue = padLeft(finalbinvalue, requiredDataBytesLen * 8, "0");
                bitmask = padLeft(bitmask, requiredDataBytesLen * 8, "0");
                String tmp = "";
                String tmpmask = "";
                for (int i = requiredDataBytesLen - 1; i >= 0 ; --i){
                    tmp += finalbinvalue.substring(i * 8, i * 8 + 8);
                    tmpmask += bitmask.substring(i * 8, i * 8 + 8);
                }
                finalbinvalue = tmp;
                bitmask = tmpmask;
            }

            char[] binaryRequest = requestasbin.toString().toCharArray();
            char[] binaryValue = finalbinvalue.toCharArray();

            if (little_endian) {
                for (int i = 0; i < bitscount; ++i) {
                    if (bitmask.charAt(i) == '1') {
                        binaryRequest[i + startBit] = binaryValue[i];
                    }
                }
            } else {
                for (int i = 0; i < bitscount; ++i) {
                    if (little_endian && bitmask.charAt(i) == '1'){
                        binaryRequest[i + startBit] = binaryValue[i];
                    } else {
                        binaryRequest[i + startBit] = binaryValue[i];
                    }
                }
            }

            BigInteger valueashex = new BigInteger(new String(binaryRequest), 2);
            String str16 = padLeft(valueashex.toString(16), bytescount*2, "0");

            for (int i = 0; i < bytescount; ++i){
                String hexpart = str16.substring(i*2, i*2 + 2);
                byte[] b = hexStringToByteArray(hexpart);
                byte_list[i + start_byte] = b[0];
            }

            return byte_list;
        }

        public String getHexValue(byte[] resp, EcuDataItem dataitem){
            int startByte = dataitem.firstbyte;
            int startBit = dataitem.bitoffset;
            int bits = bitscount;

            boolean little_endian = false;

            if (global_endian.equals("Little"))
                little_endian = true;

            if (dataitem.endian.equals("Little"))
                little_endian = true;
            if (dataitem.endian.equals("Big"))
                little_endian = false;

            int dataBytesLen = (int)(Math.ceil((float)bits / 8.0f));
            int requiredDataBytesLen = (int)(Math.ceil(((float)bits + (float)startBit) / 8.0f));
            int sb = startByte - 1;

            if ((sb + dataBytesLen) > resp.length) {
                throw new ArrayIndexOutOfBoundsException("Response too short");
            }

            String hexToBin = "";
            String hex;

            if (little_endian){
                int bitlength = requiredDataBytesLen * 8;
                for (int i = 0; i < requiredDataBytesLen; ++i){
                    byte b = resp[i+sb];
                    hexToBin = byteToBinaryString(b, 8) + hexToBin;
                }

                hexToBin = hexToBin.substring(bitlength - startBit - bitscount, bitlength - startBit);
                BigInteger bigValue = new BigInteger(hexToBin, 2);
                hex = bigValue.toString(16);
            } else {
                for (int i = 0; i < requiredDataBytesLen; ++i){
                    byte b = resp[i+sb];
                    hexToBin += byteToBinaryString(b, 8);
                }

                hexToBin = hexToBin.substring(startBit, startBit + bitscount);
                BigInteger bigValue = new BigInteger(hexToBin, 2);
                hex = bigValue.toString(16);
            }

            return padLeft(hex, dataBytesLen * 2, "0");
        }

        public String fmt(double d)
        {
            if(d == (long) d)
                return String.format(Locale.US, "%d",(long)d);
            else
                return String.format(Locale.US, "%.2f",d);
        }

        public String getDisplayValueWithUnit(byte[] resp, EcuDataItem dataitem){
            return getDisplayValue(resp, dataitem) + " " + unit;
        }

        public String getDisplayValue(byte[] resp, EcuDataItem dataItem){
            String hexval = getHexValue(resp, dataItem);
             if (bytesascii){
                 byte[] s = hexStringToByteArray(hexval);
                 return new String(s);
             }

             if (!scaled){
                 BigInteger bigInteger = new BigInteger(hexval, 16);
                 int val = bigInteger.intValue();

                 if (signed){
                     // Check that
                     if (bytescount == 1) {
                         val = hex8ToSigned(val);
                     } else if (bytescount == 2){
                         val = hex16ToSigned(val);
                     } // 32 bits are already signed
                 }

                 if (lists.containsKey(val))
                     return lists.get(val);

                 return hexval;
             }

            BigInteger bigInteger = new BigInteger(hexval, 16);
            int val = bigInteger.intValue();

            if (signed){
                if (bytescount == 1){
                    val = hex8ToSigned(val);
                } else if (bytescount == 2){
                    val = hex16ToSigned(val);
                }
            }

            if (divideby == 0.f){
                throw new ArithmeticException("Division by zero");
            }

            float res = ((float)val * step + (offset)) / divideby;

            if (!format.isEmpty()) {
                try {

                    DecimalFormat df = new DecimalFormat(format, new DecimalFormatSymbols(Locale.US));
                    return df.format(res);
                } catch (Exception e){
                    e.printStackTrace();
                }
            }
            return fmt(res);
        }
    }

    public static String integerToBinaryString(int b, int padding){
        return padLeft(Integer.toBinaryString(b), padding, "0");
    }

    public static String byteToBinaryString(int b, int padding){
        return padLeft(Integer.toBinaryString(b & 0xFF), padding, "0");
    }

    public String hexToBinary(String Hex)
    {
        BigInteger i = new BigInteger(Hex, 16);
        String Bin = i.toString(2);
        return Bin;
    }

    public static int hex8ToSigned(int val){
        return -((val) & 0x80) | (val & 0x7f);
    }

    public static int hex16ToSigned(int val){
        return -((val) & 0x8000) | (val & 0x7fff);
    }

    public static byte[] hexStringToByteArray(String s) {
        s = s.replace(" ", "");
        int len = s.length();
        byte[] data = new byte[len / 2];
        for (int i = 0, j = 0; i < len; i += 2, ++j) {
            data[j] = (byte) ((Character.digit(s.charAt(i), 16) << 4)
                    + Character.digit(s.charAt(i+1), 16));
        }
        return data;
    }

    public static String stringToHex(String string) {
        StringBuilder buf = new StringBuilder(1024);
        for (char ch: string.toCharArray()) {
            buf.append(String.format("%02x", (int) ch));
        }
        return buf.toString();
    }

    public static String padLeft(String str, int length, String padChar) {
        if (str.length() >= length)
            return str.substring(0, length);
        String pad = "";
        for (int i = 0; i < length; i++) {
            pad += padChar;
        }
        return pad.substring(str.length()) + str;
    }

    public class EcuRequest {
        public class SDS {
            public boolean nosds = true;
            public boolean plant = true;
            public boolean aftersales = true;
            public boolean engineering = true;
            public boolean supplier = true;
        }
        public int minbytes = 0;
        public int shiftbytescount = 0;
        public String replybytes;
        public String sentbytes;
        public boolean manualsend = false;
        public HashMap<String, EcuDataItem> recvbyte_dataitems;
        public HashMap<String, EcuDataItem> sendbyte_dataitems;
        public String name;
        public SDS sds;

        EcuDataItem getSendDataItem(String item){
            return sendbyte_dataitems.get(item);
        }

        EcuRequest(JSONObject json) {
            sds = new SDS();
            recvbyte_dataitems = new HashMap<>();
            sendbyte_dataitems = new HashMap<>();
            try {
                name = json.getString("name");
                if (json.has("minbytes")) minbytes = json.getInt("minbytes");
                if (json.has("shiftbytescount")) shiftbytescount = json.getInt("shiftbytescount");
                if (json.has("replybytes")) replybytes = json.getString("replybytes");
                if (json.has("manualsend")) manualsend = json.getBoolean("manualsend");
                if (json.has("sentbytes")) sentbytes = json.getString("sentbytes");

                if (json.has("deny_sds")) {
                    JSONArray denysdsobj = json.getJSONArray("deny_sds");
                    for (int i = 0; i < denysdsobj.length(); ++i){
                        String s = denysdsobj.getString(i);
                        if (s.equals("nosds")) sds.nosds = false;
                        if (s.equals("plant")) sds.plant = false;
                        if (s.equals("aftersales")) sds.aftersales = false;
                        if (s.equals("engineering")) sds.engineering = false;
                        if (s.equals("supplier")) sds.supplier = false;
                    }
                }
                if (json.has("sendbyte_dataitems")) {
                    JSONObject sbdiobj = json.getJSONObject("sendbyte_dataitems");
                    Iterator<String> keys = sbdiobj.keys();
                    while (keys.hasNext()) {
                        String key = keys.next();
                        JSONObject dataitemobj = sbdiobj.getJSONObject(key);
                        EcuDataItem dataitem = new EcuDataItem(dataitemobj, key);
                        sendbyte_dataitems.put(key, dataitem);

                    }
                }
                if (json.has("receivebyte_dataitems")) {
                    JSONObject sbdiobj = json.getJSONObject("receivebyte_dataitems");
                    Iterator<String> keys = sbdiobj.keys();
                    while (keys.hasNext()) {
                        String key = keys.next();
                        JSONObject dataitemobj = sbdiobj.getJSONObject(key);
                        EcuDataItem dataitem = new EcuDataItem(dataitemobj, key);
                        recvbyte_dataitems.put(key, dataitem);
                    }
                }
            } catch (Exception e) {
                e.printStackTrace();
            }
        }
    }

    public Ecu(InputStream is){
        String line;
        BufferedReader br;
        StringBuilder sb = new StringBuilder();

        try {
            br = new BufferedReader(new InputStreamReader(is));
            while ((line = br.readLine()) != null) {
                sb.append(line + "\n");
            }
        } catch (Exception e) {
            e.printStackTrace();
        }

        try {
            init(new JSONObject(sb.toString()));
        } catch (Exception e){
            e.printStackTrace();
        }
    }

    public Ecu(String json){
        try {
            init(new JSONObject(json));
        } catch (Exception e){
            e.printStackTrace();
        }
    }

    public EcuData getData(String dataname){
        return data.get(dataname);
    }

    public EcuRequest getRequest(String req_name){
        return requests.get(req_name);
    }

    public String getRequestData(byte[] bytes, String requestname, String dataname){
        EcuDataItem dataitem = getRequest(requestname).recvbyte_dataitems.get(dataname);
        EcuData ecudata = getData(dataname);
        return ecudata.getDisplayValue(bytes, dataitem);
    }

    public String getProtocol(){
        return protocol;
    }

    public String getFunctionnalAddress(){
        return funcaddr;
    }

    public boolean getFastInit(){
        return fastinit;
    }

    public String getTxId(){
        return ecu_send_id;
    }

    public String getRxId(){
        return ecu_recv_id;
    }

    public HashMap<String, String> getRequestValues(byte[] bytes, String requestname, boolean with_units){
        EcuRequest request = getRequest(requestname);
        HashMap<String, String> hash = new HashMap<>();
        Set<String> keys = request.recvbyte_dataitems.keySet();
        Iterator<String> it = keys.iterator();
        for (;it.hasNext();){
            String key = it.next();
            EcuDataItem dataitem = request.recvbyte_dataitems.get(key);
            EcuData ecudata = getData(key);
            if (with_units) {
                String val = ecudata.getDisplayValueWithUnit(bytes, dataitem);
                hash.put(key, val);
            } else {
                String val = ecudata.getDisplayValue(bytes, dataitem);
                hash.put(key, val);
            }
        }
        return hash;
    }

    public HashMap<String, Pair<String, String>> getRequestValuesWithUnit(byte[] bytes, String requestname){
        EcuRequest request = getRequest(requestname);
        HashMap<String, Pair<String, String>> hash = new HashMap<>();
        Set<String> keys = request.recvbyte_dataitems.keySet();
        Iterator<String> it = keys.iterator();
        for (;it.hasNext();){
            String key = it.next();
            EcuDataItem dataitem = request.recvbyte_dataitems.get(key);
            EcuData ecudata = getData(key);
            String val = ecudata.getDisplayValue(bytes, dataitem);
            String unit = ecudata.unit;
            Pair<String, String> pair = new Pair<>(val, unit);
            hash.put(key, pair);
        }
        return hash;
    }

    public static String byteArrayToHex(byte[] a) {
        StringBuilder sb = new StringBuilder(a.length * 2);
        for(byte b: a)
            sb.append(String.format("%02x", b));
        return sb.toString().toUpperCase();
    }

    public byte[] setRequestValues(String requestname, HashMap<String, Object> hash){
        EcuRequest req = getRequest(requestname);
        byte[] barray = hexStringToByteArray(req.sentbytes);
        Log.i("canapp", "Sentbytes : " + req.sentbytes);
        for (Map.Entry<String, Object> entry: hash.entrySet()){
            EcuDataItem item = req.getSendDataItem(entry.getKey());
            EcuData data = getData(entry.getKey());

            Log.i("canapp", "set key " + entry.getKey());
            if (!data.items.isEmpty() && (entry.getValue() instanceof String == true)){
                String val = (String)entry.getValue();
                if (data.items.containsKey(val)){
                    Log.i("canapp", "set key " + val + " with " + data.items.get(val));
                    barray = data.setValue(Integer.toHexString(data.items.get(val)), barray, item);
                    continue;
                } else {
                    Log.i("canapp", "key not found : " + val);
                }
            }
            barray = data.setValue(entry.getValue(), barray, item);
        }
        return barray;
    }

    public String getDefaultSDS(){
        return m_defaultSDS;
    }

    public List<List<String>> decodeDTC(String dtcRequestName, String response){
        List<List<String>> dtcList = new ArrayList<>();

        Ecu.EcuRequest dtcRequest = getRequest(dtcRequestName);
        if (dtcRequest == null)
            return dtcList;

        int shiftBytesCount = dtcRequest.shiftbytescount;
        byte[] bytesResponse = hexStringToByteArray(response);

        int numDtc = bytesResponse[1] & 0xFF;

        for (int i = 0; i < numDtc; ++i){
            HashMap<String, String> currentDTC;
            if (bytesResponse.length < shiftBytesCount)
                break;
            try {
                currentDTC = getRequestValues(bytesResponse, dtcRequestName, true);
            } catch (Exception e) {

                continue;
            }
            Iterator<String> it = currentDTC.keySet().iterator();
            List<String> currentDtcList = new ArrayList<>();
            while (it.hasNext()) {
                String key = it.next();
                if (key.equals("NDTC"))
                    continue;
                currentDtcList.add(key+":"+currentDTC.get(key));
            }
            dtcList.add(currentDtcList);
            if (bytesResponse.length >= shiftBytesCount)
                bytesResponse = Arrays.copyOfRange(bytesResponse, shiftBytesCount, bytesResponse.length);
            else
                break;
        }
        return dtcList;
    }

    public String getName(){
        return ecu_name;
    }

    private void init(JSONObject ecudef){
        requests = new HashMap<>();
        HashMap<String, EcuDevice> devices = new HashMap<>();
        data = new HashMap<>();
        sdsrequests = new HashMap<>();
        m_defaultSDS = "10C0";

        try {
            if (ecudef.has("endian")) global_endian = ecudef.getString("endian");
            if (ecudef.has("ecuname")) ecu_name = ecudef.getString("ecuname");

            if (ecudef.has("obd")) {
                JSONObject obd = ecudef.getJSONObject("obd");
                protocol = obd.getString("protocol");
                String funcname = obd.getString("funcname");
                if (protocol.equals("CAN")) {
                    ecu_send_id = obd.getString("send_id");
                    ecu_recv_id = obd.getString("recv_id");
                    if (obd.has("baudrate ")) ;

                }
                if (protocol.equals("KWP2000")) {
                    fastinit = obd.getBoolean("fastinit");
                }
                if (obd.has("funcaddr")) funcaddr = obd.getString("funcaddr");
            }

            JSONArray req_array = ecudef.getJSONArray("requests");
            for (int i = 0; i < req_array.length(); ++i) {
                JSONObject reqobj = req_array.getJSONObject(i);
                EcuRequest ecureq = new EcuRequest(reqobj);
                requests.put(ecureq.name, ecureq);
            }

            JSONArray dev_array = ecudef.getJSONArray("devices");
            for (int i = 0; i < dev_array.length(); ++i) {
                JSONObject devobj = dev_array.getJSONObject(i);
                EcuDevice ecudev = new EcuDevice(devobj);
                devices.put(ecudev.name, ecudev);
            }

            JSONObject dataobjs = ecudef.getJSONObject("data");
            Iterator<String> keys = dataobjs.keys();
            for (; keys.hasNext(); ) {
                String key = keys.next();
                JSONObject dataobj = dataobjs.getJSONObject(key);
                EcuData ecudata = new EcuData(dataobj, key);
                data.put(key, ecudata);
            }
        } catch (Exception e) {
            e.printStackTrace();
        }

        // Gather StartDiagnosticSession requests
        for (String requestName : requests.keySet()){
            String upperReqName = requestName.toUpperCase();
            if (upperReqName.contains("START")
                    && upperReqName.contains("DIAG")
                    && upperReqName.contains("SESSION")){
                // Case StartDiagnosticSession.Extended
                EcuRequest request = requests.get(requestName);
                if (upperReqName.contains("EXTENDED") && !request.sentbytes.isEmpty()){
                    m_defaultSDS = request.sentbytes;
                }
                for (String sdsDataItemName : request.sendbyte_dataitems.keySet()){

                    EcuDataItem ecuDataItem = request.sendbyte_dataitems.get(sdsDataItemName);
                    String upperSdsDataItemName = sdsDataItemName.toUpperCase();

                    if (upperSdsDataItemName.contains("SESSION") && upperSdsDataItemName.contains("NAME")){
                        for (String dataItemName: data.get(sdsDataItemName).items.keySet()) {
                            HashMap sdsBuildValues = new HashMap();
                            sdsBuildValues.put(ecuDataItem.name, dataItemName);
                            byte[] dataStream = setRequestValues(requestName, sdsBuildValues);
                            sdsrequests.put(dataItemName, byteArrayToHex(dataStream).toUpperCase());
                            if (ecuDataItem.name.toUpperCase().contains("EXTENDED")){
                                m_defaultSDS = byteArrayToHex(dataStream).toUpperCase();
                            }
                        }
                    }
                }
                if (request.sendbyte_dataitems.keySet().size() == 0){
                    sdsrequests.put(requestName, request.sentbytes);
                }
            }
        }
    }
}
