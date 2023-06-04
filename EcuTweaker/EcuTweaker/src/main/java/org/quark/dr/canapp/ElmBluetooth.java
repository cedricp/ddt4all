package org.quark.dr.canapp;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.UUID;

import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothSocket;
import android.os.Bundle;
import android.os.Handler;
import android.os.Message;

public class ElmBluetooth extends ElmBase {
    // Debugging
    private static final String TAG = "ElmBluetoothThread";
    private static final boolean D = false;
    private static final UUID SPP_UUID = UUID.fromString("0001101-0000-1000-8000-00805F9B34FB");
    private ConnectThread mConnectThread;
    private ConnectedThread mConnectedThread;
    private String mBtAddress;

    protected ElmBluetooth(Handler handler, String logDir) {
        super(handler, logDir);
    }

    @Override
    public int getMode(){
        return MODE_BT;
    }

    @Override
    public boolean connect(String address) {
        setState(STATE_CONNECTING);
        BluetoothAdapter btAdapter = BluetoothAdapter.getDefaultAdapter();
        if (btAdapter == null)
            return false;

        BluetoothDevice device;
        try {
            device = btAdapter.getRemoteDevice(address);
        } catch (Exception e){
            return false;
        }
        if (device == null)
            return false;

        disconnect();

        // Start the thread to connect with the given device
        mConnectThread = new ConnectThread(device);
        mConnectThread.start();
        mBtAddress = address;
        return true;
    }

    @Override
    public boolean reconnect(){
        return connect(mBtAddress);
    }

    public synchronized void createConnectedThread(BluetoothSocket socket, BluetoothDevice
            device) {
        // Cancel the thread that completed the connection
        if (mConnectThread != null) {
            mConnectThread.cancel();
            mConnectThread = null;
        }

        // Cancel any thread currently running a connection
        if (mConnectedThread != null) {
            mConnectedThread.cancel();
            mConnectedThread = null;
        }

        // Start the thread to manage the connection and perform transmissions
        mConnectedThread = new ConnectedThread(socket);
        mConnectedThread.start();
        synchronized (this) {
            if (mConnectionHandler != null) {
                // Send the name of the connected device back to the UI Activity
                Message msg = mConnectionHandler.obtainMessage(ScreenActivity.MESSAGE_DEVICE_NAME);
                Bundle bundle = new Bundle();
                bundle.putString(ScreenActivity.DEVICE_NAME, device.getName());
                msg.setData(bundle);
                mConnectionHandler.sendMessage(msg);
            }
        }

        setState(STATE_CONNECTED);
    }

    @Override
    public void disconnect(){
        if (mConnectThread != null) {
            mConnectThread.cancel();
        }

        if (mConnectedThread != null) {
            mConnectedThread.cancel();
        }

        mConnectThread = null;
        mConnectedThread = null;

        clearMessages();

        setState(STATE_NONE);
        synchronized (this) {
            if (mConnectionHandler != null) {
                mConnectionHandler.removeCallbacksAndMessages(null);
            }
        }
    }

    @Override
    protected String writeRaw(String raw_buffer) {
        raw_buffer += "\r";
        return mConnectedThread.write(raw_buffer);
    }

    private void connectionFailed() {
        logInfo("Bluetooth connection failed");
        setState(STATE_NONE);
    }

    private void connectionLost() {
        mRunningStatus = false;
        logInfo("Bluetooth connection lost");
        setState(STATE_DISCONNECTED);
    }

    /*
     * Connected thread class
     * Asynchronously manage ELM connection
     *
     */
    private class ConnectThread extends Thread {
        private final BluetoothSocket mmSocket;
        private final BluetoothDevice mmDevice;

        public ConnectThread(BluetoothDevice device) {
            mmDevice = device;
            BluetoothSocket tmp = null;

            /*
             * Get a BluetoothSocket for a connection with the
             * given BluetoothDevice
             */
            try {
                tmp = device.createRfcommSocketToServiceRecord(SPP_UUID);
            } catch (IOException e) {
            }
            mmSocket = tmp;
        }

        public void run() {
            String mSocketType = "ELM-socket";
            setName("ConnectThread" + mSocketType);

            // Always cancel discovery because it will slow down a connection
            BluetoothAdapter btAdapter = BluetoothAdapter.getDefaultAdapter();
            if (btAdapter == null)
                return;
            btAdapter.cancelDiscovery();

            // Make a connection to the BluetoothSocket
            try {
                // This is a blocking call and will only return on a
                // successful connection or an exception
                mmSocket.connect();
            } catch (IOException e) {
                try {
                    mmSocket.close();
                } catch (IOException e2) {
                }
                connectionFailed();
                return;
            }

            // Reset the ConnectThread because we're done
            synchronized (ElmBluetooth.this) {
                mConnectThread = null;
            }

            // Start the connected thread
            createConnectedThread(mmSocket, mmDevice);
        }

        public void cancel() {
            if (!isAlive())
                return;

            interrupt();

            try {
                mmSocket.close();
            } catch (IOException e) {
            }

            try {
                join();
            } catch (InterruptedException e) {
            }
        }
    }

    /*
     * Connect thread class
     * Asynchronously create a Bluetooth socket
     *
     */
    private class ConnectedThread extends Thread {
        private final BluetoothSocket mmSocket;
        private final InputStream mmInStream;
        private final OutputStream mmOutStream;

        public ConnectedThread(BluetoothSocket socket) {
            mMessages.clear();
            mmSocket = socket;
            InputStream tmpIn = null;
            OutputStream tmpOut = null;

            // Get the BluetoothSocket input and output streams
            // The InputStream read() method should block
            try {
                tmpIn = socket.getInputStream();
                tmpOut = socket.getOutputStream();
            } catch (IOException e) {
            }

            mmInStream = tmpIn;
            mmOutStream = tmpOut;
        }

        public void run() {
            connectedThreadMainLoop();
        }

        public void cancel() {
            mRunningStatus = false;
            interrupt();
            mMessages.clear();
            try {
                mmSocket.close();
            } catch (IOException e) {
            }

            if (!isAlive())
                return;

            try {
                join();
            } catch (InterruptedException e) {

            }
        }

        private String write(String raw_buffer) {
            byte[] reply_buffer = new byte[4096];
            try {
                mmOutStream.write(raw_buffer.getBytes());
            } catch (IOException e) {
                connectionLost();
                // Start the service over to restart listening mode
                try {
                    mmSocket.close();
                } catch (IOException ioe){

                }
                return "ERROR : DISCONNECTED";
            }

            // Wait ELM response
            int u = -1;
            while (true) {
                try {
                    // Read from the InputStream
                    u = u + 1;
                    int bytes = mmInStream.read(reply_buffer, u, 1);
                    if (bytes < 1) {
                        --u;
                        continue;
                    }

                    // Convert carriage return to line feed
                    if (reply_buffer[u] == 0x0d)
                        reply_buffer[u] = 0x0a;

                    if (reply_buffer[u] == '>') { // End of communication
                        return new String(reply_buffer, 0, u - 1);
                    }
                } catch (IOException e) {
                    connectionLost();
                    break;
                }
            }
            return "ERROR : UNKNOWN";
        }
    }
}