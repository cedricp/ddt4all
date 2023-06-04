package org.quark.dr.canapp;

import android.content.Context;
import android.os.Bundle;
import android.os.Handler;
import android.os.Message;

import org.quark.dr.ecu.EcuDatabase;
import org.quark.dr.ecu.IsoTPDecode;
import org.quark.dr.ecu.IsoTPEncode;

import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.OutputStreamWriter;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.HashMap;

import static java.lang.Math.min;

public abstract class ElmBase {
    // Constants that indicate the current connection state
    public static final int STATE_NONE = 0;
    public static final int STATE_CONNECTING = 1;
    public static final int STATE_CONNECTED = 2;
    public static final int STATE_DISCONNECTED = 3;

    public static final int MODE_WIFI = 0;
    public static final int MODE_BT = 1;
    public static final int MODE_USB = 2;

    protected ArrayList<String> mMessages;
    protected int mRxa, mTxa;
    protected HashMap<String, String> mEcuErrorCodeMap;
    protected volatile Handler mConnectionHandler;
    protected OutputStreamWriter mLogFile;
    protected String mLogDir;
    protected volatile boolean mRunningStatus;
    static protected ElmBase mSingleton = null;
    protected boolean mConnecting = false;
    private int mState;
    protected boolean mSessionActive;
    private EcuDatabase mEcuDatabase;
    private boolean mCFC0;
    private String mProtocol;

    static public ElmBase getSingleton() {
        return mSingleton;
    }

    static public ElmBase createBluetoothSingleton(Handler handler, String logDir){
        mSingleton = new ElmBluetooth(handler, logDir);
        return mSingleton;
    }

    static public ElmBase createWifiSingleton(Context context, Handler handler, String logDir){
        mSingleton = new ElmWifi(context, handler, logDir);
        return mSingleton;
    }

    static public ElmBase createSerialSingleton(Context context, Handler handler, String logDir){
        mSingleton = new ElmUsbSerial(context, handler, logDir);
        return mSingleton;
    }

    EcuDatabase getDB(){
        return mEcuDatabase;
    }

    void setDB(EcuDatabase db){
        mEcuDatabase = db;
    }

    protected static final String mEcuErrorCodeString =
            "10:General Reject," +
            "11:Service Not Supported," +
            "12:SubFunction Not Supported," +
            "13:Incorrect Message Length Or Invalid Format," +
            "21:Busy Repeat Request," +
            "22:Conditions Not Correct Or Request Sequence Error," +
            "23:Routine Not Complete," +
            "24:Request Sequence Error," +
            "31:Request Out Of Range," +
            "33:Security Access Denied- Security Access Requested," +
            "35:Invalid Key," +
            "36:Exceed Number Of Attempts," +
            "37:Required Time Delay Not Expired," +
            "40:Download not accepted," +
            "41:Improper download type," +
            "42:Can not download to specified address," +
            "43:Can not download number of bytes requested," +
            "50:Upload not accepted," +
            "51:Improper upload type," +
            "52:Can not upload from specified address," +
            "53:Can not upload number of bytes requested," +
            "70:Upload Download NotAccepted," +
            "71:Transfer Data Suspended," +
            "72:General Programming Failure," +
            "73:Wrong Block Sequence Counter," +
            "74:Illegal Address In Block Transfer," +
            "75:Illegal Byte Count In Block Transfer," +
            "76:Illegal Block Transfer Type," +
            "77:Block Transfer Data Checksum Error," +
            "78:Request Correctly Received-Response Pending," +
            "79:Incorrect ByteCount During Block Transfer," +
            "7E:SubFunction Not Supported In Active Session," +
            "7F:Service Not Supported In Active Session," +
            "80:Service Not Supported In Active Diagnostic Mode," +
            "81:Rpm Too High," +
            "82:Rpm Too Low," +
            "83:Engine Is Running," +
            "84:Engine Is Not Running," +
            "85:Engine RunTime TooLow," +
            "86:Temperature Too High," +
            "87:Temperature Too Low," +
            "88:Vehicle Speed Too High," +
            "89:Vehicle Speed Too Low," +
            "8A:Throttle/Pedal Too High," +
            "8B:Throttle/Pedal Too Low," +
            "8C:Transmission Range In Neutral," +
            "8D:Transmission Range In Gear," +
            "8F:Brake Switch(es)NotClosed (brake pedal not pressed or not applied)," +
            "90:Shifter Lever Not In Park ," +
            "91:Torque Converter Clutch Locked," +
            "92:Voltage Too High," +
            "93:Voltage Too Low";

    public abstract void disconnect();
    public abstract boolean connect(String address);
    public abstract boolean reconnect();
    public abstract int getMode();

    protected abstract String writeRaw(String raw_buffer);
    public boolean hasDevicePermission(){
        return true;
    }
    public void requestPermission(){
    }


    public ElmBase(Handler handler, String logDir) {
        mProtocol = "UNDEFINED";
        mMessages = new ArrayList<>();
        mConnectionHandler = handler;
        mLogFile = null;
        mLogDir = logDir;
        mRxa = mTxa = -1;
        mSessionActive = false;
        mState = STATE_NONE;
        mCFC0 = false;
        createLogFile();
        buildMaps();
    }

    public void setSoftFlowControl(boolean b){
        mCFC0 = b;
    }

    public void changeHandler(Handler h) {
        synchronized (this) {
            if (mConnectionHandler != null) {
                mConnectionHandler.removeCallbacksAndMessages(null);
                mConnectionHandler = null;
            }

            mSessionActive = false;
            mConnectionHandler = h;
        }

        if (mConnectionHandler == null)
            clearMessages();

        // Force UI to recover connection status
        if (mConnectionHandler != null) {
            if (mState == STATE_CONNECTING) {
                setState(STATE_CONNECTING);
            } else if (mState == STATE_CONNECTED) {
                setState(STATE_CONNECTED);
            } else {
                setState(STATE_DISCONNECTED);
            }
        }
    }

    protected void setState(int state) {
        mState = state;
        // Give the new state to the Handler so the UI Activity can update
        synchronized (this) {
            if (mConnectionHandler != null) {
                mConnectionHandler.obtainMessage(ScreenActivity.MESSAGE_STATE_CHANGE, state, -1)
                        .sendToTarget();
            }
        }
    }

    public int getState() {
        return mState;
    }

    protected void logInfo(String log) {
        synchronized (this) {
            if (mConnectionHandler != null) {
                Message msg = mConnectionHandler.obtainMessage(ScreenActivity.MESSAGE_LOG);
                Bundle bundle = new Bundle();
                bundle.putString(ScreenActivity.TOAST, log);
                msg.setData(bundle);
                mConnectionHandler.sendMessage(msg);
            }
        }
    }

    protected void createLogFile() {
        File file = new File(mLogDir + "/log.txt");
        if (!file.exists()) {
            try {
                boolean ok = file.createNewFile();
                if(!ok){
                    logInfo("Log file create error");
                }
            } catch (IOException e) {
                logInfo("Log file create error : " + e.getMessage());
                e.printStackTrace();
            }
        }
        try {
            FileOutputStream fileOutputStream = new FileOutputStream(file, true);
            mLogFile = new OutputStreamWriter(fileOutputStream);
        } catch (FileNotFoundException e) {
            logInfo("Log file output stream error : " + e.getMessage());
            e.printStackTrace();
        }
        try {
            mLogFile.append(getTimeStamp()).append(" Log file created\n");
            mLogFile.flush();
        } catch (Exception e){
            logInfo("Log file write error : " + e.getMessage());
            e.printStackTrace();
        }
    }

    public void flushLogs() {
        if (mLogFile != null) {
            try {
                mLogFile.flush();
            } catch (IOException e){
                e.printStackTrace();
            }
        }
    }

    public void closeLogFile(){
        if (mLogFile != null){
            flushLogs();
            try {
                mLogFile.close();
            } catch (IOException e){
                e.printStackTrace();
            }
        }
    }

    protected String getTimeStamp() {
        return "[" + new SimpleDateFormat("dd-MM-hh:mm:ss")
                .format(new Date()) + "] ";
    }

    public void initElm() {
        mProtocol = "UNDEFINED";
        logInfo("Re-intializing ELM...");
        write("AT Z");        // reset ELM
    }

    public void initCan(String rxa, String txa) {
        logInfo("Intializing CAN protocol...");
        mProtocol = "CAN";
        write("AT E1");
        write("AT S0");
        write("AT H0");
        write("AT L0");
        write("AT AL");
        write("AT CAF0");

        write("AT SP 6");
        write("AT SH " + txa);
        write("AT CRA " + rxa.toUpperCase());
        write("AT FC SH " + txa.toUpperCase());
        write("AT FC SD 30 00 00");
        write("AT FC SM 1");
        mRxa = Integer.parseInt(rxa, 16);
        mTxa = Integer.parseInt(txa, 16);
        if (mCFC0)
            write("AT CFC0");
    }

    private void initIso(){
        write("AT WS");
        write("AT E1");
        write("AT L0");
        write("AT D1");
        write("AT H0");
        write("AT AL");
        write("AT KW0");
    }

    public void initKwp(String addr, boolean fastInit) {
        logInfo("Intializing KPW2000 protocol...");
        mProtocol = "KWP2000";
        mRxa = 0xF1;
        mTxa = Integer.parseInt(addr, 16);

        initIso();

        write("AT SH 81 " + addr + " F1");
        write("AT SW 96");
        write("AT WM 81 " + addr + " F1 3E");
        write("AT IB10");
        write("AT ST FF");
        write("AT AT 0");

        if (!fastInit) {
            write("AT SP 4");
            write("AT IIA " + addr);
            write("AT SI");
        } else {
            write("AT SP 5");
            write("AT FI");
        }

        write("AT AT 1");
    }

    public void initIso8(String addr) {
        logInfo("Intializing ISO8 protocol...");
        mProtocol = "ISO8";
        mRxa = 0xF1;
        mTxa = Integer.parseInt(addr, 16);

        initIso();

        write("AT SH 81 " + addr + " F1");
        write("AT SW 96");
        write("AT WM 81 " + addr + " F1 3E");
        write("AT IB10");
        write("AT ST FF");
        write("AT SP 3");
        write("AT AT 0");
        write("AT SI");
        write("AT AT 1");
    }

    public void setTimeOut(int timeOut) {
        int timeout = (timeOut / 4);
        if (timeout > 255)
            timeout = 255;
        write("AT ST " + Integer.toHexString(timeout));
    }

    public void buildMaps() {
        mEcuErrorCodeMap = new HashMap<>();
        String[] ERRC = mEcuErrorCodeString.replace(" ", "").split(",");
        for (String erc : ERRC) {
            String[] idToAddr = erc.split(":");
            mEcuErrorCodeMap.put(idToAddr[0], idToAddr[1]);
        }
    }

    public String getEcuErrorCode(String hexError) {
        return mEcuErrorCodeMap.get(hexError);
    }

    public boolean isHexadecimal(String text) {
        char[] hexDigits = {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
                'a', 'b', 'c', 'd', 'e', 'f', 'A', 'B', 'C', 'D', 'E', 'F'};

        for (char symbol : text.toCharArray()) {
            boolean found = false;
            for (char hexDigit : hexDigits) {
                if (symbol == hexDigit) {
                    found = true;
                    break;
                }
            }
            if (!found)
                return false;
        }
        return true;
    }

    public synchronized void clearMessages(){
        mMessages.clear();
    }

    protected void connectedThreadMainLoop() {
        long timer = System.currentTimeMillis();
        mRunningStatus = true;

        /*
         * Keep listening to the InputStream while connected
         * Thread can be stopped by switching the running status member
         */
        while (mRunningStatus) {
            String message = "";
            int num_queue = 0;
            boolean messagePresent = false;

            // Synchronized message extraction
            synchronized (this) {
                if ( ! ElmBase.this.mMessages.isEmpty() ) {
                    message = mMessages.get(0);
                    mMessages.remove(0);
                    num_queue = mMessages.size();
                    messagePresent = true;
                }
            }

            if (messagePresent){
                int message_len = message.length();
                if ((message_len > 6) && message.substring(0, 6).equalsIgnoreCase("DELAY:")) {
                    int delay = Integer.parseInt(message.substring(6));
                    try {
                        Thread.sleep(delay);
                    } catch (InterruptedException e) {
                        break;
                    }
                } else if ((message_len > 2) && message.substring(0, 2).equalsIgnoreCase("AT")) {
                    String result = writeRaw(message);
                    result = message + ";" + result;

                    int result_length = result.length();
                    byte[] tmpbuf = new byte[result_length];
                    System.arraycopy(result.getBytes(), 0, tmpbuf, 0, result_length);
                    synchronized (this) {
                        if (mConnectionHandler != null) {
                            mConnectionHandler.obtainMessage(ScreenActivity.MESSAGE_READ,
                                    result_length, mTxa, tmpbuf).sendToTarget();
                            mConnectionHandler.obtainMessage(ScreenActivity.MESSAGE_QUEUE_STATE,
                                    num_queue, -1, null).sendToTarget();
                        }
                    }
                } else {
                    if (mProtocol.equals("CAN")) {
                        if (mCFC0)
                            sendCanCFC0(message);
                        else
                            sendCan(message);
                    } else {
                        // KWP / ISO8
                        sendISO(message);
                    }

                    synchronized (this) {
                        if (mConnectionHandler != null) {
                            mConnectionHandler.obtainMessage(ScreenActivity.MESSAGE_QUEUE_STATE,
                                    num_queue, -1, null).sendToTarget();
                        }
                    }
                    // Reset tester_present timer
                    // This can speed up things
                    timer = System.currentTimeMillis();
                }
            }

            try {
                Thread.sleep(10);
            } catch (InterruptedException e) {
                break;
            }

            // Keep session alive
            if (mProtocol.equals("CAN") && mSessionActive && ((System.currentTimeMillis() - timer) > 1500) && mRxa > 0) {
                timer = System.currentTimeMillis();
                writeRaw("013E");
            }
        }
        mRunningStatus = false;
        setState(STATE_DISCONNECTED);
    }

    void setSessionActive(boolean active) {
        mSessionActive = active;
    }

    protected void sendISO(String message){
        String messageResult = writeRaw(message);

        // Parse response
        StringBuilder resultMess = new StringBuilder();
        for (String s : messageResult.split("\n")){
            // Remove useless whitespaces
            String cleanedMessage = s.replace(" ", "");
            if (cleanedMessage.equals(message)){
                // Echo cancellation
                continue;
            }
            resultMess.append(cleanedMessage);
        }

        String result = resultMess.toString();

        try {
            if (mLogFile != null) {
                mLogFile.append("ISO SENT: ").append(getTimeStamp()).append(message).append("\n");
                mLogFile.append("ISO RECV: ").append(getTimeStamp()).append(result).append("\n");
            }
        } catch (IOException e) {
            logInfo("Log error : " + e.getMessage());
        }

        result = message + ";" + result;

        int result_length = result.length();
        byte[] tmpbuf = new byte[result_length];
        //Make copy for not to rewrite in other thread
        System.arraycopy(result.getBytes(), 0, tmpbuf, 0, result_length);
        synchronized (this) {
            if (mConnectionHandler != null) {
                mConnectionHandler.obtainMessage(ScreenActivity.MESSAGE_READ, result_length, -1, tmpbuf).sendToTarget();
            }
        }
    }

    protected void sendCanCFC0(String message){
        if (!isHexadecimal(message))
            return;

        IsoTPEncode isotpm = new IsoTPEncode(message);
        // Encode ISO_TP data
        ArrayList<String> raw_command = isotpm.getFormattedArray();
        ArrayList<String> responses = new ArrayList<>();
        boolean noerrors = true;
        String errorMsg = "";
        boolean ATR1 = true;

        int BS = 1; // Burst size
        int ST = 0; // Frame interval
        int Fc = 0; // Current frame
        int Fn = raw_command.size();

        // Set ELM timeout to 300ms for first frame response
        if (Fn > 1 && raw_command.get(0).length() > 15){
            writeRaw("ATST4B");
        }

        while(Fc < Fn){
            String frsp;
            if (!ATR1){
                writeRaw("ATR1");
                ATR1 = true;
            }
            long tb = System.currentTimeMillis();

            if (Fn > 1 && Fc == (Fn - 1)){
                writeRaw("ATSTFF");
                writeRaw("ATAT1");
            }

            String currentRawCommand = raw_command.get(Fc);
            if (Fc == 0 || Fc == (Fn-1) && currentRawCommand.length() < 16){
                // We'll get only 1 frame: nr, fc, ff or sf
                frsp = writeRaw(currentRawCommand + '1');
            } else {
                frsp = writeRaw(currentRawCommand );
            }

            ++Fc;

            ArrayList<String> s0 = new ArrayList<>();
            for (String s: frsp.split("\n")){
                // Echo cancellation
                int raw_cmd_len = raw_command.get(Fc-1).length();
                String subs = s ;
                if (subs.length() > raw_cmd_len)
                    subs = s.substring(0, raw_cmd_len);
                if (subs.equals(raw_command.get(Fc-1)))
                    continue;

                s = s.replace(" ", "");
                if(s.isEmpty())
                    continue;

                if (isHexadecimal(s))
                    s0.add(s);
            }

            for (String s: s0){
                // Some data
                if (s.charAt(0) == '3'){
                    // Flow control frame

                    // Extract burst size
                    String bs;
                    if (s.length() >= 3)
                        bs = s.substring(2, 4);
                    else
                        bs = "03";

                    BS = Integer.parseInt(bs, 16);

                    // Extract frame interval
                    String frameInterval;
                    if (s.length() >= 5)
                        frameInterval = s.substring(4, 6);
                    else
                        frameInterval = "EF";
                    if (frameInterval.toUpperCase().charAt(0) == 'F'){
                        ST = Integer.parseInt(frameInterval.substring(1,2), 16) * 100;
                    } else {
                        ST = Integer.parseInt(frameInterval, 16);
                    }
                    break;
                } else if (s.startsWith("037F") && s.startsWith("78", 6)) {
                    if (s0.size() > 0 && s.equals(s0.get(s0.size()-1))){
                        noerrors = false;
                        errorMsg = "Cannot handle 037F78 yet !";
                        break;
                        // Heavy method here !!
                    } else {
                        continue;
                    }
                } else {
                    responses.add(s);
                    continue;
                }
            }

            // Number of frames to send without response
            int cf = min(BS - 1, (Fn - Fc) - 1);

            if (cf > 0){
                writeRaw("ATR0");
                ATR1 = false;
            }

            while (cf > 0){
                --cf;

                long tc = System.currentTimeMillis();
                if ((tc - tb) < ST){
                    try {
                        Thread.sleep(ST - (tc - tb));
                    } catch (InterruptedException ie){
                        return;
                    }
                }
                tb = tc;

                frsp = writeRaw(raw_command.get(Fc));
                ++Fc;
            }
        }

        StringBuilder result = new StringBuilder();
        if (responses.size() != 1){
            noerrors = false;
            errorMsg = "Cannot send CAN frame with software flow control";
        } else {
            int nbytes = 0;
            String response0 = responses.get(0);
            if (response0.charAt(0) == '0'){
                // Single frame
                nbytes = Integer.parseInt(response0.substring(1,2), 16);
                result = new StringBuilder(responses.get(0).substring(2, 2 + (nbytes * 2)));
            } else if (response0.charAt(0) == '1') {
                nbytes = Integer.parseInt(response0.substring(1, 4), 16);
                // We assume that it should be more than 7
                nbytes -= 6;
                int nframes = 1 + nbytes / 7 + ((nbytes%7) > 0 ? 1 : 0);
                int cframe = 1;
                result = new StringBuilder(response0.substring(4, 16));

                while (cframe < nframes){
                    String sBS =  String.format("%x", min(nframes - responses.size(), 0xf));
                    String frsp = writeRaw("300" + sBS + "00" + sBS);

                    // Analyse response
                    boolean nodataflag = false;
                    for (String s: frsp.split("\n")){
                        // Echo cancel
                        if (s.startsWith(raw_command.get(Fc - 1))){
                            continue;
                        }

                        if (s.contains("NO DATA")){
                            nodataflag = true;
                            break;
                        }

                        s = s.replace(" ", "");
                        if (s.isEmpty()){
                            continue;
                        }

                        if (isHexadecimal(s)){
                            responses.add(s);
                            if (s.charAt(0) == '2'){
                                // Consecutive frame
                                int tmp_fn = Integer.parseInt(s.substring(1,2), 16);
                                if (tmp_fn != (cframe % 16)){
                                    noerrors = false;
                                    errorMsg = "Multiline software flow control lost frame";
                                    continue;
                                }
                                ++cframe;
                                result.append(s, 2, 16);
                            }
                            continue;
                        }

                        if (nodataflag){
                            break;
                        }
                    }
                }
            } else {
                noerrors = false;
                errorMsg = "CFC0 first frame omitted";
            }
        }

        if (!noerrors){
            message = "ERROR : " + errorMsg;
        } else {
            // Decode received ISO_TP data
            IsoTPDecode isotpdec = new IsoTPDecode(responses);
            result = new StringBuilder(isotpdec.decodeCan());
        }

        try {
            if (mLogFile != null) {
                mLogFile.append("CAN CFC SENT: ").append(getTimeStamp()).append(message).append("\n");
                mLogFile.append("CAN CFC RECV: ").append(getTimeStamp()).append(result.toString()).append("\n");
            }
        } catch (IOException e) {
            logInfo("Log error : " + e.getMessage());
            e.printStackTrace();
        }

        result.insert(0, message + ";");
        int result_length = result.length();
        byte[] tmpbuf = new byte[result_length];
        //Make copy for not to rewrite in other thread
        System.arraycopy(result.toString().getBytes(), 0, tmpbuf, 0, result_length);
        synchronized (this) {
            if (mConnectionHandler != null) {
                mConnectionHandler.obtainMessage(ScreenActivity.MESSAGE_READ, result_length, -1, tmpbuf).sendToTarget();
            }
        }
    }

    protected void sendCan(String message){
        IsoTPEncode isotpm = new IsoTPEncode(message);
        // Encode ISO_TP data
        ArrayList<String> raw_command = isotpm.getFormattedArray();
        ArrayList<String> responses = new ArrayList<>();
        boolean error = false;
        StringBuilder errorMsg = new StringBuilder();

        // Send data
        for (String frame: raw_command) {
            String frsp = writeRaw(frame);

            for(String s: frsp.split("\n")){
                // Remove unwanted characters
                s = s.replace("\n", "");
                // Echo cancellation
                if (s.equals(frame))
                    continue;

                // Remove whitespaces
                s = s.replace(" ", "");
                if (s.length() == 0)
                    continue;

                if (isHexadecimal(s)){
                    // Filter out frame control (FC) response
                    if (s.charAt(0) == '3')
                        continue;
                    responses.add(s);
                } else {
                    errorMsg.append(frsp);
                    error = true;
                }
            }
        }

        String result;
        if (error){
            result = "ERROR : " + errorMsg;
        } else {
            // Decode received ISO_TP data
            IsoTPDecode isotpdec = new IsoTPDecode(responses);
            result = isotpdec.decodeCan();
        }

        try {
            if (mLogFile != null) {
                mLogFile.append("CAN SENT: ").append(getTimeStamp()).append(message).append("\n");
                mLogFile.append("CAN RECV: ").append(getTimeStamp()).append(result).append("\n");
            }
        } catch (IOException e) {
            logInfo("Log error : " + e.getMessage());
            e.printStackTrace();
        }

        result = message + ";" + result;
        int result_length = result.length();
        byte[] tmpbuf = new byte[result_length];
        //Make copy for not to rewrite in other thread
        System.arraycopy(result.getBytes(), 0, tmpbuf, 0, result_length);
        synchronized (this) {
            if (mConnectionHandler != null) {
                mConnectionHandler.obtainMessage(ScreenActivity.MESSAGE_READ, result_length, -1, tmpbuf).sendToTarget();
            }
        }
    }

    public synchronized void write(String out) {
        mMessages.add(out);
    }

    public void setEcuName(String name){
        if (mLogFile != null){
            try {
                mLogFile.append("New session with ECU ").append(name).append("\n");
            } catch (IOException e){
                e.printStackTrace();
            }
        }
    }
}
