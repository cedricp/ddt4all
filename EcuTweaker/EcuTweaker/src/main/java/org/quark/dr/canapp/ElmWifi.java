package org.quark.dr.canapp;

import android.content.Context;
import android.net.wifi.WifiInfo;
import android.net.wifi.WifiManager;
import android.os.Bundle;
import android.os.Handler;
import android.os.Message;
import android.util.Log;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.net.Socket;

public class ElmWifi extends ElmBase{
    private static final String TAG = "ElmWifiThread";
    private final Context mContext;
    private Socket mSocket;
    private WifiManager.WifiLock wifiLock;

    private String mServerIPAddress = "192.168.0.10";
    private static final int mServerPort = 35000;
    private String mDeviceName = "Elm327";
    private ElmWifi.ConnectedThread mConnectedThread;
    private ElmWifi.ConnectThread mConnectThread;

    protected ElmWifi(Context context, Handler handler, String logDir) {
        super(handler, logDir);
        mContext = context;
    }

    private void connectionLost(String message) {
        // Send a failure message back to the Activity;
        logInfo("Wifi device connection was lost : " + message);
        mRunningStatus = false;
        setState(STATE_DISCONNECTED);
    }

    @Override
    public int getMode(){
        return MODE_WIFI;
    }

    @Override
    public boolean connect(String address) {
        if (!address.isEmpty()) {
            mServerIPAddress = address;
        }

        disconnect();
        setState(STATE_CONNECTING);

        WifiManager wifi = (WifiManager) mContext.getApplicationContext().getSystemService(Context.WIFI_SERVICE);

        if (wifi == null){
            return false;
        }

        if (wifiLock == null) {
            wifiLock = wifi.createWifiLock(WifiManager.WIFI_MODE_FULL_HIGH_PERF, "HighPerf wifi lock");
        }

        if (wifiLock == null){
            return false;
        }

        wifiLock.acquire();
        WifiInfo wifiInfo = wifi.getConnectionInfo();
        String name = wifiInfo.getSSID();

        if (wifi.isWifiEnabled() && (name.toUpperCase().contains("OBD") ||
                name.toUpperCase().contains("ELM") ||
                name.toUpperCase().contains("ECU") ||
                name.toUpperCase().contains("LINK") ) ) {
            mConnecting = true;
            mDeviceName = name.replace("\"","");
            synchronized (this) {
                if (mConnectionHandler != null) {
                    mConnectionHandler.removeCallbacksAndMessages(null);
                }
            }

            mConnectThread = new ElmWifi.ConnectThread(mServerIPAddress, mServerPort);
            mConnectThread.start();

            return true;
        }

        logInfo("Unable to connect wifi device");
        setState(STATE_DISCONNECTED);

        mConnecting = false;
        return false;
    }

    @Override
    public boolean reconnect(){
        return connect(mServerIPAddress);
    }

    @Override
    public void disconnect() {
        if (mConnectThread != null)
            mConnectThread.cancel();

        if (mConnectedThread != null)
            mConnectedThread.cancel();

        if (wifiLock != null && wifiLock.isHeld())
            wifiLock.release();

        clearMessages();

        synchronized (this) {
            if (mConnectionHandler != null) {
                mConnectionHandler.removeCallbacksAndMessages(null);
            }
        }
        mConnecting = false;

        setState(STATE_NONE);
    }

    private void createConnectedThread(Socket socket){
        mSocket = socket;
        mConnectedThread = new ElmWifi.ConnectedThread(socket);
        mConnectedThread.start();
        setState(STATE_CONNECTED);
    }

    public boolean isConnected() {
        return (mSocket != null) && mSocket.isConnected() && mRunningStatus;
    }

    @Override
    protected String writeRaw(String raw_buffer) {
        raw_buffer += "\r";
        return mConnectedThread.write(raw_buffer.getBytes());
    }


    /*
     * Connected thread class
     * Asynchronously manage ELM connection
     *
     */
    private class ConnectedThread extends Thread {
        private final Socket mmSocket;
        private final OutputStream mOutStream;
        private final InputStream mInStream;

        public ConnectedThread(Socket socket) {
            mmSocket = socket;
            InputStream tmpIn = null;
            OutputStream tmpOut = null;

            // Get the BluetoothSocket input and output streams
            try {
                tmpIn = socket.getInputStream();
                tmpOut = socket.getOutputStream();
            } catch (IOException e) {
                Log.e(TAG, "temp sockets not created", e);
            }

            mInStream = tmpIn;
            mOutStream = tmpOut;
        }

        public void run() {
            connectedThreadMainLoop();
        }

        public String write(byte[] buffer) {
            writeToElm(buffer);
            return readFromElm();
        }

        public void writeToElm(byte[] buffer) {
            try {
                if(mmSocket != null)
                {
                    mOutStream.write(buffer);
                    mOutStream.flush();
                }
            } catch (Exception localIOException1) {
                connectionLost(localIOException1.getMessage());
                try {
                    mmSocket.close();
                } catch (IOException e){

                }
            }
        }

        public String readFromElm() {
            while (true) {
                try {
                    if(mmSocket != null)
                    {
                        byte b;
                        StringBuilder res = new StringBuilder();
                        int charCount = 0;
                        while ((char) (b = (byte) mInStream.read()) != '>') {
                            if (++charCount > 32768){
                                try {
                                    mmSocket.close();
                                } catch (IOException e){

                                }
                                connectionLost("WiFi Socket overflow");
                                return "";
                            }
                            if (b == 0x0d)
                                b = 0x0a;
                            res.append((char) b);
                        }
                        return res.toString();
                    }

                } catch (IOException localIOException) {
                    connectionLost(localIOException.getMessage());
                    break;
                } catch (Exception e) {
                    connectionLost(e.getMessage());
                    break;
                }
            }
            return "";
        }

        public void cancel() {
            mRunningStatus = false;
            interrupt();

            try {
                mmSocket.close();
            } catch (IOException e) {
                Log.e(TAG, "close() of connect " + mmSocket + " socket failed", e);
            }

            try {
                join();
            } catch (InterruptedException e) {

            }
        }
    }

    /*
     * Connect thread class
     * Asynchronously create a Wifi socket
     *
     */
    private class ConnectThread extends Thread {
        private final String mServerIp;
        private final int mServerPort;
        private Socket mLocalSocket;

        public ConnectThread(String serverIp, int serverPort) {
            mServerIp = serverIp;
            mServerPort = serverPort;
        }

        public void run() {
            try {
                mLocalSocket = new Socket();
                mLocalSocket.connect(new InetSocketAddress(mServerIp, mServerPort), 6000);
                mLocalSocket.setKeepAlive(true);
                mLocalSocket.setSoTimeout(4000);
                setState(STATE_CONNECTED);
                mConnecting = false;

                // Send the name of the connected device back to the UI Activity
                synchronized (this) {
                    if (mConnectionHandler != null) {
                        Message msg = mConnectionHandler.obtainMessage(ScreenActivity.MESSAGE_DEVICE_NAME);
                        Bundle bundle = new Bundle();
                        bundle.putString(ScreenActivity.DEVICE_NAME, mDeviceName);
                        msg.setData(bundle);
                        mConnectionHandler.sendMessage(msg);
                    }
                }

                if (mConnectedThread != null) {
                    mConnectedThread.cancel();
                    mConnectedThread = null;
                }

                synchronized (this){
                    mMessages.clear();
                }

                // Start the thread to manage the connection and perform transmissions
                createConnectedThread(mLocalSocket);
                mConnecting = false;
                return;
            } catch (IOException e) {
                System.out.println(">>> Except");
                e.printStackTrace();
            }
            setState(STATE_DISCONNECTED);
        }

        public void cancel() {
            interrupt();

            try {
                mLocalSocket.close();
            } catch (IOException e) {
            }

            try {
                join();
            } catch (InterruptedException e) {
            }
        }
    }
}