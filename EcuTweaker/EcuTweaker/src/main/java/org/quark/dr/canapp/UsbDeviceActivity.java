package org.quark.dr.canapp;
/* Copyright 2011-2013 Google Inc.
 * Copyright 2013 mike wakerly <opensource@hoho.com>
 *
 * This library is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public
 * License as published by the Free Software Foundation; either
 * version 2.1 of the License, or (at your option) any later version.
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public
 * License along with this library; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301,
 * USA.
 *
 * Project home page: https://github.com/mik3y/usb-serial-for-android
 */

import android.app.Activity;
import android.app.PendingIntent;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.hardware.usb.UsbDevice;
import android.hardware.usb.UsbDeviceConnection;
import android.hardware.usb.UsbManager;
import android.os.AsyncTask;
import android.os.Bundle;
import android.os.Handler;
import android.os.Message;
import android.os.SystemClock;
import androidx.annotation.NonNull;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ArrayAdapter;
import android.widget.ListView;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.TwoLineListItem;

import org.quark.dr.usbserial.driver.UsbSerialDriver;
import org.quark.dr.usbserial.driver.UsbSerialPort;
import org.quark.dr.usbserial.driver.UsbSerialProber;
import org.quark.dr.usbserial.util.HexDump;

import java.io.IOException;
import java.lang.ref.WeakReference;
import java.util.ArrayList;
import java.util.List;

/**
 * Shows a {@link ListView} of available USB devices.
 *
 * @author mike wakerly (opensource@hoho.com)
 */
public class UsbDeviceActivity extends Activity {

    private final String TAG = DeviceListActivity.class.getSimpleName();
    public static String EXTRA_DEVICE_SERIAL = "device_serial";

    private UsbManager mUsbManager;
    private ListView mListView;
    private TextView mProgressBarTitle;
    private ProgressBar mProgressBar;

    private static PendingIntent mPermissionIntent;
    private static final int MESSAGE_REFRESH = 101;
    private static final long REFRESH_TIMEOUT_MILLIS = 5000;
    private static final String ACTION_USB_PERMISSION = "org.quark.dr.canapp.USB_PERMISSION";
    private static UsbSerialPort mCurrentUsbSerial = null;

    private final Handler mHandler = new Handler() {
        @Override
        public void handleMessage(Message msg) {
            switch (msg.what) {
                case MESSAGE_REFRESH:
                    refreshDeviceList();
                    mHandler.sendEmptyMessageDelayed(MESSAGE_REFRESH, REFRESH_TIMEOUT_MILLIS);
                    break;
                default:
                    super.handleMessage(msg);
                    break;
            }
        }

    };

    private final BroadcastReceiver mReceiver = new BroadcastReceiver() {
        public void onReceive(Context context, Intent intent) {
            String action = intent.getAction();
            if (mCurrentUsbSerial == null) {
                return;
            }
            if (ACTION_USB_PERMISSION.equals(action)) {
                synchronized (this) {
                    if (intent.getBooleanExtra(UsbManager.EXTRA_PERMISSION_GRANTED, false)) {
                        UsbDeviceConnection connection =
                                mUsbManager.openDevice(mCurrentUsbSerial.getDriver().getDevice());
                        // Shouldn't happen, but who knows...
                        if (connection == null)
                            return;
                        try{
                            mCurrentUsbSerial.open(connection);
                        } catch (IOException e){
                            return;
                        }

                        Intent intentResult = new Intent();
                        intentResult.putExtra(EXTRA_DEVICE_SERIAL, mCurrentUsbSerial.getSerial());
                        // Set result and finish this Activity
                        UsbDeviceActivity.this.setResult(Activity.RESULT_OK, intentResult);
                        finish();
                    }
                }
            }
        }
    };

    private final List<UsbSerialPort> mEntries = new ArrayList<>();
    private ArrayAdapter<UsbSerialPort> mAdapter;

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.usbmain);

        mPermissionIntent = PendingIntent.getBroadcast(getApplicationContext(),
                0,
                new Intent(ACTION_USB_PERMISSION), PendingIntent.FLAG_IMMUTABLE);
        mUsbManager = (UsbManager) getSystemService(Context.USB_SERVICE);
        mListView = findViewById(R.id.deviceList);
        mProgressBar = findViewById(R.id.progressBar);
        mProgressBarTitle = findViewById(R.id.progressBarTitle);

        mAdapter = new ArrayAdapter<UsbSerialPort>(this,
                android.R.layout.simple_expandable_list_item_2, mEntries) {
            @Override
            public View getView(int position, View convertView, @NonNull ViewGroup parent) {
                final TwoLineListItem row;
                if (convertView == null){
                    final LayoutInflater inflater =
                            (LayoutInflater) getSystemService(Context.LAYOUT_INFLATER_SERVICE);
                    row = (TwoLineListItem) inflater.inflate(android.R.layout.simple_list_item_2, null);
                } else {
                    row = (TwoLineListItem) convertView;
                }

                final UsbSerialPort port = mEntries.get(position);
                final UsbSerialDriver driver = port.getDriver();
                final UsbDevice device = driver.getDevice();

                final String title = String.format("Vendor %s Product %s",
                        HexDump.toHexString((short) device.getVendorId()),
                        HexDump.toHexString((short) device.getProductId()));
                row.getText1().setText(title);

                final String subtitle = driver.getClass().getSimpleName();
                row.getText2().setText(subtitle);

                return row;
            }
        };

        mListView.setAdapter(mAdapter);
        mListView.setOnItemClickListener((parent, view, position, id) -> {
            Log.d(TAG, "Pressed item " + position);
            if (position >= mEntries.size()) {
                Log.w(TAG, "Illegal position.");
                return;
            }

            final UsbSerialPort port = mEntries.get(position);

            // Create the result Intent and include the MAC address
            Intent intent = new Intent();
            String usbaddr;

            // Check permissions
            if (mUsbManager.hasPermission(port.getDriver().getDevice())) {
                // Permission OK
                UsbDeviceConnection connection =
                        mUsbManager.openDevice(port.getDriver().getDevice());

                if (connection != null) {
                    try {
                        port.open(connection);
                        usbaddr = port.getSerial();
                        intent.putExtra(EXTRA_DEVICE_SERIAL, usbaddr);
                        // All is OK. set result and finish this Activity
                        setResult(Activity.RESULT_OK, intent);
                        finish();
                    } catch (IOException e) {
                        Log.e("canapp", "USB Activity, connection failed");
                        intent.putExtra(EXTRA_DEVICE_SERIAL, "CONNECTION FAILED");
                        setResult(Activity.RESULT_CANCELED, intent);
                        finish();
                    }
                } else {
                    Log.e("canapp", "USB Activity, unable to create connection");
                    intent.putExtra(EXTRA_DEVICE_SERIAL, "CANNOT CREATE CONNECTION");
                    setResult(Activity.RESULT_CANCELED, intent);
                    finish();
                }
            } else {
                // Request permission
                mCurrentUsbSerial = port;
                mUsbManager.requestPermission(port.getDriver().getDevice(), mPermissionIntent);
            }
        });

        getApplicationContext().registerReceiver(mReceiver, new IntentFilter(ACTION_USB_PERMISSION));
    }

    @Override
    protected void onResume() {
        super.onResume();
        mHandler.sendEmptyMessage(MESSAGE_REFRESH);
    }

    @Override
    protected void onPause() {
        super.onPause();
        mHandler.removeMessages(MESSAGE_REFRESH);
    }

    private void refreshDeviceList() {
        showProgressBar();
        new SearchUSBTask(this).execute();
    }

    private static class SearchUSBTask extends AsyncTask<Void, Void, List<UsbSerialPort>> {
        private final WeakReference<UsbDeviceActivity> mActivity;
        SearchUSBTask(UsbDeviceActivity activity){
            mActivity =  new WeakReference<>(activity);
        }
        @Override
        protected List<UsbSerialPort> doInBackground(Void... params) {
            SystemClock.sleep(1000);

            final List<UsbSerialDriver> drivers =
                    UsbSerialProber.getDefaultProber().findAllDrivers(mActivity.get().mUsbManager);

            final List<UsbSerialPort> result = new ArrayList<>();
            for (final UsbSerialDriver driver : drivers) {
                final List<UsbSerialPort> ports = driver.getPorts();
                result.addAll(ports);
            }

            return result;
        }

        @Override
        protected void onPostExecute(List<UsbSerialPort> result) {
            mActivity.get().mEntries.clear();
            mActivity.get().mEntries.addAll(result);
            mActivity.get().mAdapter.notifyDataSetChanged();
            mActivity.get(). mProgressBarTitle.setText(
                    String.format("%s device(s) found", mActivity.get().mEntries.size()));
            mActivity.get().hideProgressBar();
        }

    }

    private void showProgressBar() {
        mProgressBar.setVisibility(View.VISIBLE);
        mProgressBarTitle.setText("Refreshing");
    }

    private void hideProgressBar() {
        mProgressBar.setVisibility(View.INVISIBLE);
    }
}
