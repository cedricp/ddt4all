package org.quark.dr.canapp;

import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.hardware.usb.UsbDeviceConnection;
import android.hardware.usb.UsbManager;
import android.os.Handler;

import org.quark.dr.usbserial.driver.UsbSerialDriver;
import org.quark.dr.usbserial.driver.UsbSerialPort;
import org.quark.dr.usbserial.driver.UsbSerialProber;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

public class ElmUsbSerial extends ElmBase {
    private static UsbSerialPort msPort = null;
    private final Context mContext;
    private ConnectedThread mConnectedThread;
    private String mUsbSerial;
    private static PendingIntent mPermissionIntent;

    private static final String ACTION_USB_PERMISSION = "org.quark.dr.canapp.USB_PERMISSION";

    ElmUsbSerial(Context context, Handler handler, String logDir) {
        super(handler, logDir);
        mContext = context;
        mPermissionIntent = PendingIntent.getBroadcast(context,
                0,
                new Intent(ACTION_USB_PERMISSION), PendingIntent.FLAG_IMMUTABLE);
    }

    @Override
    public int getMode(){
        return MODE_USB;
    }

    @Override
    public boolean connect(String serial) {
        setState(STATE_DISCONNECTED);
        mUsbSerial = serial;
        msPort = null;
        final UsbManager usbManager = (UsbManager) mContext.getApplicationContext().getSystemService(Context.USB_SERVICE);

        if (usbManager == null)
            return false;

        final List<UsbSerialDriver> drivers =
                UsbSerialProber.getDefaultProber().findAllDrivers(usbManager);

        final List<UsbSerialPort> result = new ArrayList<>();
        for (final UsbSerialDriver driver : drivers) {
            final List<UsbSerialPort> ports = driver.getPorts();
            result.addAll(ports);
            for (UsbSerialPort port : ports){
                if (!usbManager.hasPermission(port.getDriver().getDevice())){
                    logInfo("No permission to access USB device " + serial);
                }
                UsbDeviceConnection connection = usbManager.openDevice(port.getDriver().getDevice());
                if (connection == null){
                    logInfo("USB : error opening device connection");
                    continue;
                }
                try {
                    port.open(connection);
                    if (port.getSerial().equals(mUsbSerial)) {
                        msPort = port;
                        break;
                    } else {
                        msPort = null;
                        port.close();
                    }
                } catch (IOException e) {
                    logInfo("USB : error opening port");
                }
            }
        }

        if (msPort == null){
            return false;
        }

        try {
            msPort.setParameters(38400, 8, UsbSerialPort.STOPBITS_1, UsbSerialPort.PARITY_NONE);
        } catch (IOException e) {
            try {
                msPort.close();
            } catch (IOException e2) {

            }
            logInfo("USB : error setting port parameters" + e.getMessage());
            msPort = null;
            return false;
        } catch (Exception e) {
            logInfo("USB : error setting port parameters : " + e.getMessage());
        }
        logInfo("USB : Interface successfully connected");
        // Launch thread
        mConnectedThread = new ConnectedThread(msPort);
        mConnectedThread.start();
        setState(STATE_CONNECTED);
        return true;
    }

    @Override
    public boolean reconnect(){
        disconnect();
        return connect(mUsbSerial);
    }

    @Override
    public void disconnect() {
        if (mConnectedThread != null)
            mConnectedThread.cancel();

        clearMessages();

        synchronized (this) {
            if (mConnectionHandler != null) {
                mConnectionHandler.removeCallbacksAndMessages(null);
            }
        }
        mConnecting = false;

        setState(STATE_NONE);
    }

    @Override
    protected String writeRaw(String raw_buffer) {
        raw_buffer += "\r";
        return mConnectedThread.write(raw_buffer.getBytes());
    }

    private void connectionLost(String message) {
        // Send a failure message back to the Activity;
        logInfo("USB device connection was lost : " + message);
        mRunningStatus = false;
        setState(STATE_DISCONNECTED);
    }

    /*
     * Connected thread class
     * Asynchronously manage ELM connection
     *
     */
    private class ConnectedThread extends Thread {
        private final UsbSerialPort mUsbSerialPort;

        public ConnectedThread(UsbSerialPort usbSerialPort) {
            mUsbSerialPort = usbSerialPort;
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
                if(mUsbSerialPort != null)
                {
                    byte[] arrayOfBytes = buffer;
                    mUsbSerialPort.write(arrayOfBytes, 500);
                }
            } catch (Exception localIOException1) {
                connectionLost("USBWRITE IO Exception : " +  localIOException1.getMessage());
                try {
                    mUsbSerialPort.close();
                } catch (IOException e){

                }
            }
        }

        public String readFromElm() {
            StringBuilder final_res = new StringBuilder();
            while (true) {
                byte[] bytes = new byte[2048];
                int bytes_count = 0;
                long millis =System.currentTimeMillis();
                if(mUsbSerialPort != null)
                {
                    try {
                        bytes_count = mUsbSerialPort.read(bytes, 1500);
                    } catch (IOException e){
                        logInfo("USB read IO exception : " + e.getMessage());
                        bytes_count = 0;
                    } catch (NullPointerException pne){
                        connectionLost("USB read exception (closing) : " + pne.getMessage());
                        break;
                    } catch (Exception e) {
                        logInfo("USB read exception : " + e.getMessage());
                    }

                    if (bytes_count > 0){
                        boolean eof = false;
                        String res = new String(bytes, 0, bytes_count);
                        res = res.substring(0, bytes_count);

                        if(res.length() > 0) {
                            // Only break when ELM has sent termination char
                            if (res.charAt(res.length() - 1) == '>') {
                                if (res.length() > 2)
                                    res = res.substring(0, res.length() - 2);
                                else
                                    res = "";
                                eof = true;
                            }
                            res = res.replaceAll("\r", "\n");
                            final_res.append(res);
                            if (eof)
                                break;
                        }
                    } else {
                        try {
                            Thread.sleep(5);
                        } catch (Exception e){

                        }
                    }
                    if ((System.currentTimeMillis() - millis) > 4000){
                        connectionLost("USB read : Timeout");
                        break;
                    }

                }
            }
            return final_res.toString();
        }

        public void cancel() {
            mRunningStatus = false;
            interrupt();

            try {
                mUsbSerialPort.close();
            } catch (IOException e) {
            }

            try {
                join();
            } catch (InterruptedException e) {
            }
        }
    }

    @Override
    public boolean hasDevicePermission(){
        if (msPort == null)
            return true;
        final UsbManager usbManager = (UsbManager) mContext.getApplicationContext().getSystemService(Context.USB_SERVICE);
        if( usbManager == null) return false;
        return usbManager.hasPermission(msPort.getDriver().getDevice());
    }

    @Override
    public void requestPermission(){
        if (msPort == null)
            return;
        final UsbManager usbManager = (UsbManager) mContext.getApplicationContext().getSystemService(Context.USB_SERVICE);
        if (usbManager == null) return;
        usbManager.requestPermission(msPort.getDriver().getDevice(), mPermissionIntent);
    }
}
