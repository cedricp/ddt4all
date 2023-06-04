package org.quark.dr.canapp;

import android.Manifest;
import android.app.Activity;
import android.app.AlertDialog;
import android.app.ProgressDialog;
import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.os.AsyncTask;
import android.os.Bundle;
import android.os.Environment;
import android.os.Handler;
import android.os.Message;
import android.provider.Settings;
import androidx.annotation.NonNull;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;
import androidx.appcompat.app.AppCompatActivity;
import android.text.Html;
import android.text.Spanned;
import android.text.method.ScrollingMovementMethod;
import android.util.Log;
import android.view.Gravity;
import android.view.LayoutInflater;
import android.view.View;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.ImageButton;
import android.widget.ImageView;
import android.widget.ListView;
import android.widget.TextView;
import android.widget.Toast;

import org.quark.dr.ecu.Ecu;
import org.quark.dr.ecu.EcuDatabase;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.math.BigInteger;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.Date;
import java.util.Objects;
import java.util.Timer;
import java.util.TimerTask;

import static org.quark.dr.canapp.ElmBase.MODE_BT;
import static org.quark.dr.canapp.ElmBase.MODE_USB;
import static org.quark.dr.canapp.ElmBase.MODE_WIFI;
import static org.quark.dr.canapp.ElmBluetooth.STATE_CONNECTED;
import static org.quark.dr.canapp.ElmBluetooth.STATE_CONNECTING;
import static org.quark.dr.canapp.ElmBluetooth.STATE_DISCONNECTED;
import static org.quark.dr.canapp.ElmBluetooth.STATE_NONE;
import static org.quark.dr.canapp.ScreenActivity.MESSAGE_DEVICE_NAME;
import static org.quark.dr.canapp.ScreenActivity.MESSAGE_LOG;
import static org.quark.dr.canapp.ScreenActivity.MESSAGE_QUEUE_STATE;
import static org.quark.dr.canapp.ScreenActivity.MESSAGE_READ;
import static org.quark.dr.canapp.ScreenActivity.MESSAGE_STATE_CHANGE;
import static org.quark.dr.canapp.ScreenActivity.MESSAGE_TOAST;
import static org.quark.dr.canapp.ScreenActivity.TOAST;

public class MainActivity extends AppCompatActivity {
    final static String TAG = "EcuTweaker";
    final static int PERMISSIONS_ACCESS_EXTERNAL_STORAGE = 0;
    final static int PERMISSIONS_ACCESS_COARSE_LOCATION = 1;
    final static int PERMISSIONS_WRITE_EXTERNAL_STORAGE = 2;
    // Intent request codes
    private static final int    REQUEST_CONNECT_DEVICE = 1;
    private static final int    REQUEST_SCREEN         = 2;
    private static final int    REQUEST_ENABLE_BT      = 3;
    public static final String  DEFAULT_PREF_TAG = "default";

    public static final int     LINK_WIFI=0;
    public static final int     LINK_BLUETOOTH=1;
    public static final int     LINK_USB=2;

    public static final String PREF_DEVICE_ADDRESS = "btAdapterAddress";
    public static final String PREF_DEVICE_USBSERIAL = "usbSerialNumber";
    public static final String PREF_GLOBAL_SCALE = "globalScale";
    public static final String PREF_FONT_SCALE = "fontScale";
    public static final String PREF_ECUZIPFILE = "ecuZipFile";
    public static final String PREF_PROJECT = "project";
    public static final String PREF_LINK_MODE =  "BT";
    public static final String PREF_SOFTFLOW = "softFlowControl";

    public static String mLastLog;
    private EcuDatabase mEcuDatabase;
    private TextView mStatusView;
    private Button mBtButton;
    private ImageButton mLinkChooser;
    private ImageView mBtIconImage;
    private ListView mEcuListView, mSpecificEcuListView;
    private ArrayList<EcuDatabase.EcuInfo> mCurrentEcuInfoList;
    private String mEcuFilePath, mBtDeviceAddress, mUsbSerialNumber, mCurrentProject;
    private int mCurrentEcuAddressId;
    private TextView mViewSupplier, mViewDiagVersion, mViewVersion, mViewSoft, mLogView;

    private ElmBase mObdDevice;
    private Handler mHandler = null;
    private EcuDatabase.EcuIdentifierNew mEcuIdentifierNew = null;
    private Timer mConnectionTimer;
    private LicenseLock mLicenseLock;
    private int mLinkMode;
    private boolean mActivateBluetoothAsked;
    private ProgressDialog mScanProgressDialog;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        initialize();
    }

    private String readFileAsString(String filePath) {
        StringBuilder result = new StringBuilder("No log file found");
        File file = new File(filePath);
        if ( file.exists() ) {
            result = new StringBuilder();
            FileInputStream fis = null;
            try {
                fis = new FileInputStream(file);
                char current;
                while (fis.available() > 0) {
                    current = (char) fis.read();
                    result.append(current);
                }
            } catch (Exception e) {
                e.printStackTrace();
            } finally {
                if (fis != null)
                    try {
                        fis.close();
                    } catch (IOException ignored) {
                    }
            }
        }
        return result.toString();
    }

    private void initialize(){
        long id = new BigInteger(Settings.Secure.getString(getContentResolver(),
                Settings.Secure.ANDROID_ID), 16).longValue();
        mLicenseLock = new LicenseLock(id);
        SharedPreferences defaultPrefs = this.getSharedPreferences(DEFAULT_PREF_TAG, MODE_PRIVATE);
        String linkMode = defaultPrefs.getString(PREF_LINK_MODE, "BT");

        mCurrentProject = "";
        mCurrentEcuAddressId = -1;
        mActivateBluetoothAsked = false;

        mHandler = new MainActivity.messageHandler(this);
        mObdDevice = null;

        mStatusView = findViewById(R.id.statusView);
        mBtButton = findViewById(R.id.btButton);
        mEcuListView = findViewById(R.id.ecuListView);
        mSpecificEcuListView = findViewById(R.id.deviceView);
        Button mScanButton = findViewById(R.id.buttonScan);
        ImageButton mChooseProjectButton = findViewById(R.id.projectButton);
        mLinkChooser = findViewById(R.id.linkChooser);
        mBtIconImage = findViewById(R.id.btIcon);
        mViewDiagVersion = findViewById(R.id.textViewDiagversion);
        mViewSupplier = findViewById(R.id.textViewSupplier);
        mViewSoft = findViewById(R.id.textViewSoft);
        mViewVersion = findViewById(R.id.textViewVersion);
        mLogView = findViewById(R.id.logView);

        mLogView.setGravity(Gravity.BOTTOM);
        mLogView.setMovementMethod(new ScrollingMovementMethod());
        mLogView.setBackgroundResource(R.drawable.edittextroundgreen);
        mLogView.setTextIsSelectable(true);

        mBtIconImage.setColorFilter(Color.RED);

        if (linkMode.equals("BT")) {
            mLinkMode = LINK_BLUETOOTH;
        } else if (linkMode.equals("WIFI")){
            mLinkMode = LINK_WIFI;
        } else {
            mLinkMode = LINK_USB;
        }
        setLink();

        Button viewLogButton = findViewById(R.id.viewLogButton);
        viewLogButton.setOnClickListener(v -> {
            try {
                MainActivity.this.copyLogs();
                return;
            } catch (IOException e){
                mLogView.append("Error : Cannot copy logs\n");
            }

            mLastLog = readFileAsString(
                    MainActivity.this.getApplicationContext().getFilesDir().
                            getAbsolutePath() + "/log.txt");
            System.out.println("?? "  + MainActivity.this.getApplicationContext().getFilesDir().
                    getAbsolutePath());
            LayoutInflater inflater= LayoutInflater.from(MainActivity.this);
            View view = inflater.inflate(R.layout.custom_scroll, null);

            TextView textview = view.findViewById(R.id.textmsg);
            textview.setEnabled(true);
            textview.setText(mLastLog);
            AlertDialog.Builder alertDialog = new AlertDialog.Builder(MainActivity.this);
            alertDialog.setTitle("LOGS");
            alertDialog.setView(view);
            AlertDialog alert = alertDialog.create();
            alert.setButton(AlertDialog.BUTTON_NEUTRAL,getResources().
                    getString(R.string.COPY_TO_CLIPBOARD),
                    (dialog, which) -> {
                        ClipboardManager  clipboard = (ClipboardManager) getSystemService(CLIPBOARD_SERVICE);
                        ClipData clip = ClipData.newPlainText("EcuTeakerLog", mLastLog);
                        if(clipboard != null) clipboard.setPrimaryClip(clip);
                    });
            alert.show();
        });

        Button clearLogButton = findViewById(R.id.clearLogButton);

        clearLogButton.setOnClickListener(v -> Toast.makeText(getApplicationContext(),
                getResources().getString(R.string.LONGPRESS_TO_DELETE),
                Toast.LENGTH_SHORT).show());

        clearLogButton.setOnLongClickListener(v -> {
            String logFilename = MainActivity.this.getApplicationContext().getFilesDir().
                    getAbsolutePath() + "/log.txt";
            File logFile = new File(logFilename);
            if (logFile.exists()){
                if (logFile.delete()){
                    Toast.makeText(getApplicationContext(),
                            getResources().getString(R.string.LOGFILE_DELETED),
                            Toast.LENGTH_SHORT).show();
                } else {
                    Toast.makeText(getApplicationContext(),
                            getResources().getString(R.string.LOGFILE_DELETE_FAILED),
                            Toast.LENGTH_SHORT).show();
                }
            }
            return true;
        });

        mScanButton.setOnClickListener(v -> onScanBus());

        mBtButton.setOnClickListener(v -> selectDevice());

        mEcuListView.setOnItemClickListener((parent, view, position, id1) -> {
            String info = ((TextView) view).getText().toString();
            ecuTypeSelected(info, mCurrentProject);
        });

        mSpecificEcuListView.setOnItemClickListener((parent, view, position, id12) -> {
            if ( mCurrentEcuInfoList == null || mEcuFilePath == null){
                return;
            }
            String stringToSearch = ((TextView)view).getText().toString();
            for (EcuDatabase.EcuInfo ecuinfo : mCurrentEcuInfoList){
                if (stringToSearch.equals(ecuinfo.ecuName)){
                    startScreen(mEcuFilePath, ecuinfo.href);
                    break;
                }
            }
        });

//        ImageButton licenseButton = findViewById(R.id.licenseButton);
//        licenseButton.setOnClickListener(new View.OnClickListener() {
//            @Override
//            public void onClick(View v) {
//                onLicenseCheck();
//            }
//        });

        mChooseProjectButton.setOnClickListener(v -> chooseProject());

        mLinkChooser.setOnClickListener(v -> {
            if (mLinkMode == LINK_WIFI) {
                mLinkMode = LINK_BLUETOOTH;
            } else if (mLinkMode == LINK_BLUETOOTH) {
                mLinkMode = LINK_USB;
            } else {
                mLinkMode = LINK_WIFI;
            }
            setLink();
            System.out.println("?? " + mLinkMode);
        });

        mBtDeviceAddress = defaultPrefs.getString(PREF_DEVICE_ADDRESS, "");
        mUsbSerialNumber = defaultPrefs.getString(PREF_DEVICE_USBSERIAL, "");

        mEcuDatabase = new EcuDatabase();
        mEcuIdentifierNew = mEcuDatabase.new EcuIdentifierNew();

        if (ContextCompat.checkSelfPermission(this,
                Manifest.permission.READ_EXTERNAL_STORAGE)
                == PackageManager.PERMISSION_GRANTED){
            parseDatabase();
        } else {
            askStoragePermission();
        }

        if (ContextCompat.checkSelfPermission(this,
                Manifest.permission.WRITE_EXTERNAL_STORAGE)
                != PackageManager.PERMISSION_GRANTED){
            askStorageWritePermission();
        }

        if (ContextCompat.checkSelfPermission(this,
                Manifest.permission.ACCESS_COARSE_LOCATION)
                != PackageManager.PERMISSION_GRANTED) {
            askLocationPermission();
        }

        mLogView.append("EcuTweaker " + BuildConfig.BUILD_TYPE + " "
                + getResources().getString(R.string.VERSION) + "\n");
    }

    private void setLink(){
        /*
         * First disconnect chat
         */
        if (mObdDevice != null)
            mObdDevice.disconnect();

        SharedPreferences defaultPrefs = this.getSharedPreferences(DEFAULT_PREF_TAG, MODE_PRIVATE);
        SharedPreferences.Editor edit = defaultPrefs.edit();
        if (mLinkMode == LINK_BLUETOOTH){
            mLinkChooser.setImageResource(R.drawable.ic_bt_connected);
            mBtButton.setEnabled(true);
            edit.putString(PREF_LINK_MODE, "BT");
            edit.apply();

            BluetoothAdapter btAdapter = BluetoothAdapter.getDefaultAdapter();
            if (!mActivateBluetoothAsked && btAdapter != null && !btAdapter.isEnabled()){
                mActivateBluetoothAsked = true;
                Intent enableIntent = new Intent(BluetoothAdapter.ACTION_REQUEST_ENABLE);
                startActivityForResult(enableIntent, REQUEST_ENABLE_BT);
            }
        } else if (mLinkMode == LINK_WIFI){
            mActivateBluetoothAsked = false;
            mLinkChooser.setImageResource(R.drawable.ic_wifi);
            mBtButton.setEnabled(false);
            edit.putString(PREF_LINK_MODE, "WIFI");
            edit.apply();
        }  else {
            mActivateBluetoothAsked = false;
            mLinkChooser.setImageResource(R.drawable.ic_usb);
            mBtButton.setEnabled(true);
            edit.putString(PREF_LINK_MODE, "USB");
            edit.apply();
        }
    }

//    private void onLicenseCheck(){
//        AlertDialog.Builder builder = new AlertDialog.Builder(this);
//        builder.setTitle(getResources().getString(R.string.APP_ENTER_CODE));
//        builder.setMessage(getResources().getString(R.string.USER_REQUEST_CODE) + " : "
//                + mLicenseLock.getPublicCode());
//        final EditText input = new EditText(this);
//        input.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_PASSWORD);
//        builder.setView(input);
//
//        builder.setPositiveButton(getResources().getString(R.string.OK), new DialogInterface.OnClickListener() {
//            @Override
//            public void onClick(DialogInterface dialog, int which) {
//                mLicenseLock.checkUnlock(input.getText().toString());
//                setLicenseSatus();
//            }
//        });
//        builder.setNegativeButton(getResources().getString(R.string.CANCEL), new DialogInterface.OnClickListener() {
//            @Override
//            public void onClick(DialogInterface dialog, int which) {
//                dialog.cancel();
//            }
//        });
//
//        builder.show();
//    }

    private void startConnectionTimer(){
        stopConnectionTimer();

        TimerTask timertask = new TimerTask() {
            @Override
            public void run() {
                if(!isChatConnected() && !isChatConnecting())
                    connectDevice();
            }
        };

        mConnectionTimer = new Timer();
        mConnectionTimer.schedule(timertask, 1000, 4000);
    }

    private void stopConnectionTimer(){
        if (mConnectionTimer != null) {
            mConnectionTimer.cancel();
            mConnectionTimer.purge();
            mConnectionTimer = null;
        }
    }

//    private void setLicenseSatus(){
//        if (mLicenseLock.isLicenseOk()){
//            mLogView.append(getResources().getString(R.string.APP_UNLOCKED) + "\n");
//            (findViewById(R.id.licenseButton)).setEnabled(false);
//            SharedPreferences defaultPrefs = this.getSharedPreferences(DEFAULT_PREF_TAG,
//                    MODE_PRIVATE);
//            SharedPreferences.Editor edit = defaultPrefs.edit();
//            edit.putString(PREF_LICENSE_CODE, mLicenseLock.getPrivateCode());
//            edit.apply();
//            ((ImageButton)findViewById(R.id.licenseButton)).setColorFilter(Color.GREEN);
//        } else {
//            ((ImageButton)findViewById(R.id.licenseButton)).setColorFilter(Color.RED);
//            mLogView.append(getResources().getString(R.string.WRONG_CODE) + "\n");
//        }
//    }

    private void connectDevice() {
        if (mObdDevice != null){
            if ((mObdDevice.getMode() == MODE_BT) && (mLinkMode == LINK_BLUETOOTH)){
                if (mBtDeviceAddress.isEmpty())
                    return;
                // No need to recreate ELM manager instance
                // Address may have changed, though
                mObdDevice.connect(mBtDeviceAddress);
                return;
            }

            if ((mObdDevice.getMode() == MODE_WIFI) && (mLinkMode == LINK_WIFI)){
                // No need to recreate ELM manager instance
                mObdDevice.reconnect();
                return;
            }

            if ((mObdDevice.getMode() == MODE_USB) && (mLinkMode == LINK_USB)){{
                mObdDevice.connect(mUsbSerialNumber);
                return;
            }}
        }

        String filesDir = getApplicationContext().getFilesDir().getAbsolutePath();
        if (mLinkMode == LINK_BLUETOOTH) {
            BluetoothAdapter btAdapter = BluetoothAdapter.getDefaultAdapter();
            if (btAdapter != null && !btAdapter.isEnabled()){
                return;
            }

            mObdDevice = ElmBase.createBluetoothSingleton(mHandler, filesDir);
            // address is the device MAC address
            // Get the BluetoothDevice object
            if (btAdapter == null || mBtDeviceAddress.isEmpty() || isChatConnected())
                return;

            BluetoothDevice device = btAdapter.getRemoteDevice(mBtDeviceAddress);
            if (device == null)
                return;
            // Attempt to connect to the device
            mObdDevice.connect(mBtDeviceAddress);
        } else if (mLinkMode == LINK_WIFI) {
            mObdDevice = ElmBase.createWifiSingleton(getApplicationContext(), mHandler, filesDir);
            mObdDevice.connect("");
        } else {
            mObdDevice = ElmBase.createSerialSingleton(getApplicationContext(), mHandler, filesDir);
            mObdDevice.connect(mUsbSerialNumber);
        }

        try {
            if (!mObdDevice.hasDevicePermission()) {
                mObdDevice.requestPermission();
            }
        } catch (Exception e){
            mLogView.append("Exception when trying to get permission : " + e.getMessage() + "\n");
        }
    }

    void initBus(String protocol, boolean fastinit){
        if (isChatConnected()) {
            if (protocol.equals("CAN")) {
                String txa = mEcuDatabase.getTxAddressById(mCurrentEcuAddressId);
                String rxa = mEcuDatabase.getRxAddressById(mCurrentEcuAddressId);
                if (rxa == null || txa == null)
                    return;
                mObdDevice.initCan(rxa, txa);
            } else if (protocol.equals("KWP2000")){
                String hexAddr = Ecu.padLeft(Integer.toHexString(mCurrentEcuAddressId),
                        2, "0");
                // TODO : Check slow init mode
                mObdDevice.initKwp(hexAddr, fastinit);
            } else if (protocol.equals("ISO8")){
                String hexAddr = Ecu.padLeft(Integer.toHexString(mCurrentEcuAddressId),
                        2, "0");
                // TODO : Check slow init mode
                mObdDevice.initIso8(hexAddr);
            }
        }
    }

    void showWaitDialog(){
        mScanProgressDialog = new ProgressDialog(this);
        mScanProgressDialog.setTitle("Scanning");
        mScanProgressDialog.setMessage("Please wait...");
        mScanProgressDialog.setButton(DialogInterface.BUTTON_NEGATIVE, getResources().getString(R.string.CANCEL), (dialog, which) -> {
            // Fast recovery, clear message queue to
            // avoid lags
            mObdDevice.clearMessages();
            stopProgressDialog();
        });
        mScanProgressDialog.show();
    }

    void onScanBus(){
        if(!isChatConnected()){
            Toast.makeText(this, "No ELM connection", Toast.LENGTH_SHORT).show();
            return;
        }
        AlertDialog alertDialog = new AlertDialog.Builder(MainActivity.this).create();
        alertDialog.setTitle("SELECT BUS");
        alertDialog.setButton(AlertDialog.BUTTON_POSITIVE, "CAN",
                (dialog, which) -> {
                    showWaitDialog();
                    scanBus();
                    scanBusNew();
                });

        alertDialog.setButton(AlertDialog.BUTTON_NEUTRAL, "KWP",
                (dialog, which) -> {
                    showWaitDialog();
                    scanBusKWP();
                });
        alertDialog.show();
    }

    void scanBus(){
        if(!isChatConnected()){
            Toast.makeText(this, "No ELM connection", Toast.LENGTH_SHORT).show();
            return;
        }

        if (mCurrentEcuInfoList == null || mCurrentEcuInfoList.isEmpty()) {
            Toast.makeText(this, "Select an ECU type to auto identify", Toast.LENGTH_SHORT).show();
            return;
        }
        mObdDevice.changeHandler(mHandler);
        mObdDevice.setSessionActive(false);
        mObdDevice.initElm();
        initBus("CAN", false);
        mObdDevice.setTimeOut(1000);
        /*
         * (older) ECUs gives their identifiers with 2180 command
         */
        sendCmd("10C0");
        sendCmd("2180");
    }

    void scanBusKWP(){
        if(!isChatConnected()){
            return;
        }

        if (mCurrentEcuInfoList == null || mCurrentEcuInfoList.isEmpty())
            return;
        mObdDevice.changeHandler(mHandler);
        mObdDevice.setSessionActive(false);
        mObdDevice.initElm();
        // Try slow init
        initBus("KWP2000", false);
        mObdDevice.setTimeOut(1000);
        /*
         * (old) ECUs gives their identifiers with 2180 command
         */
        sendCmd("10C0");
        sendCmd("2180");

        // Try fast init
        initBus("KWP2000", true);
        mObdDevice.setTimeOut(1000);
        sendCmd("10C0");
        sendCmd("2180");
    }

    void scanBusNew(){
        if(!isChatConnected()){
            return;
        }

        if (mObdDevice == null || mCurrentEcuInfoList == null || mCurrentEcuInfoList.isEmpty())
            return;

        mEcuIdentifierNew.reInit(mCurrentEcuAddressId);
        mObdDevice.changeHandler(mHandler);
        mObdDevice.setSessionActive(false);
        mObdDevice.initElm();
        initBus("CAN", false);
        mObdDevice.setTimeOut(1000);
        /*
         * (new) ECUs gives their identifiers with these commands
         */
        sendCmd("1003");
        sendCmd("22F1A0");
        sendCmd("22F18A");
        sendCmd("22F194");
        sendCmd("22F195");
    }

    void ecuTypeSelected(String type, String project){
        mSpecificEcuListView.setBackgroundColor(Color.BLACK);

        int ecuAddress = mEcuDatabase.getAddressByFunction(type);
        if (ecuAddress < 0) {
            mSpecificEcuListView.setAdapter(null);
            return;
        }
        mCurrentEcuAddressId = ecuAddress;
        ArrayList<EcuDatabase.EcuInfo> ecuArray = mEcuDatabase.getEcuInfo(ecuAddress);
        mCurrentEcuInfoList = ecuArray;
        if (ecuArray == null) {
            mSpecificEcuListView.setAdapter(null);
            return;
        }
        ArrayList<String> ecuNames = new ArrayList<>();
        for(EcuDatabase.EcuInfo info : ecuArray){
            if (project.isEmpty() || info.projects.contains(project))
                ecuNames.add(info.ecuName);
        }
        Collections.sort(ecuNames);
        ArrayAdapter<String> adapter;

        adapter= new ArrayAdapter<>(this,
                android.R.layout.simple_list_item_1,
                ecuNames);
        mSpecificEcuListView.setAdapter(adapter);
    }

    void selectDevice(){
        BluetoothAdapter bluetoothAdapter = BluetoothAdapter.getDefaultAdapter();

        // If the adapter is null, then Bluetooth is not supported
        if (bluetoothAdapter == null) {
            return;
        }

        if (bluetoothAdapter.isEnabled()) {
            stopConnectionTimer();
            try {
                if (mLinkMode == LINK_BLUETOOTH) {
                    Intent serverIntent = new Intent(this, DeviceListActivity.class);
                    startActivityForResult(serverIntent, REQUEST_CONNECT_DEVICE);
                } else if (mLinkMode == LINK_USB) {
                    Intent serverIntent = new Intent(this, UsbDeviceActivity.class);
                    startActivityForResult(serverIntent, REQUEST_CONNECT_DEVICE);
                }
            } catch (android.content.ActivityNotFoundException e) {

            }
        }
    }

    void startScreen(String ecuFile, String ecuHREFName){
        stopConnectionTimer();

        if (mEcuDatabase == null){
            return;
        }

        // Remove handler
        mObdDevice.changeHandler(null);
        mObdDevice.setDB(mEcuDatabase);

        try {
            Intent serverIntent = new Intent(this, ScreenActivity.class);
            Bundle b = new Bundle();
            b.putString("ecuFile", ecuFile);
            b.putString("ecuRef", ecuHREFName);
            b.putString("deviceAddress", mBtDeviceAddress);
            b.putBoolean("licenseOk", mLicenseLock.isLicenseOk());
            b.putInt("linkMode", mLinkMode);
            serverIntent.putExtras(b);
            startActivityForResult(serverIntent, REQUEST_SCREEN);
        } catch (android.content.ActivityNotFoundException e) {

        }
    }

    void askStoragePermission(){
        if (ContextCompat.checkSelfPermission(this,
                Manifest.permission.READ_EXTERNAL_STORAGE)
                != PackageManager.PERMISSION_GRANTED) {
            if (ActivityCompat.shouldShowRequestPermissionRationale(this,
                    Manifest.permission.READ_EXTERNAL_STORAGE)) {
                Toast.makeText(this,
                        "You need external storage permission to use this application",
                        Toast.LENGTH_SHORT).show();
                ActivityCompat.requestPermissions(this,
                        new String[]{Manifest.permission.READ_EXTERNAL_STORAGE},
                        PERMISSIONS_ACCESS_EXTERNAL_STORAGE);
            } else {
                ActivityCompat.requestPermissions(this,
                        new String[]{Manifest.permission.READ_EXTERNAL_STORAGE},
                        PERMISSIONS_ACCESS_EXTERNAL_STORAGE);
            }
        } else {
            parseDatabase();
        }
    }

    void askStorageWritePermission(){
        if (ContextCompat.checkSelfPermission(this,
                Manifest.permission.WRITE_EXTERNAL_STORAGE)
                != PackageManager.PERMISSION_GRANTED) {
            if (ActivityCompat.shouldShowRequestPermissionRationale(this,
                    Manifest.permission.WRITE_EXTERNAL_STORAGE)) {
                Toast.makeText(this,
                        "You may need write storage permission to use this application",
                        Toast.LENGTH_SHORT).show();
            } else {
                ActivityCompat.requestPermissions(this,
                        new String[]{Manifest.permission.WRITE_EXTERNAL_STORAGE},
                        PERMISSIONS_WRITE_EXTERNAL_STORAGE);
            }
        }
    }

    void askLocationPermission(){
        int permissionCheck = ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_COARSE_LOCATION);
        if (permissionCheck != PackageManager.PERMISSION_GRANTED){
            if (ActivityCompat.shouldShowRequestPermissionRationale(this, Manifest.permission.ACCESS_COARSE_LOCATION)){
                Toast.makeText(this, "You need location permission to connect to WiFi", Toast.LENGTH_SHORT).show();
            }else{
                ActivityCompat.requestPermissions(this,
                        new String[]{Manifest.permission.ACCESS_COARSE_LOCATION},
                        PERMISSIONS_ACCESS_COARSE_LOCATION);
            }
        }
    }

    @Override
    public void onRequestPermissionsResult(int requestCode,
                                           @NonNull String[] permissions,
                                           @NonNull int[] grantResults) {
        switch (requestCode) {
            case PERMISSIONS_ACCESS_EXTERNAL_STORAGE: {
                // If request is cancelled, the result arrays are empty.
                if (grantResults.length > 0
                        && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                    parseDatabase();
                }
            }
        }
    }

    @Override
    public void onDestroy()
    {
        super.onDestroy();
        stopConnectionTimer();
        if (mObdDevice != null) {
            mObdDevice.disconnect();
            mObdDevice.closeLogFile();
        }
    }

    @Override
    public void onStop()
    {
        super.onStop();
        stopConnectionTimer();
    }

    @Override
    public void onStart() {
        super.onStart();
        if (mObdDevice == null)
            mObdDevice = ElmBase.getSingleton();
        if (mObdDevice != null){
            mObdDevice.changeHandler(mHandler);
            mObdDevice.setSessionActive(false);
        }
        startConnectionTimer();
    }

    @Override
    public void onActivityResult(int requestCode, int resultCode, Intent data) {
        switch (requestCode) {
            case REQUEST_CONNECT_DEVICE:
                // When DeviceListActivity returns with a device to connect
                if (resultCode == Activity.RESULT_OK) {
                    SharedPreferences defaultPrefs = this.getSharedPreferences(DEFAULT_PREF_TAG,
                            MODE_PRIVATE);
                    SharedPreferences.Editor edit = defaultPrefs.edit();
                    if (Objects.requireNonNull(data.getExtras()).containsKey(DeviceListActivity.EXTRA_DEVICE_ADDRESS)) {
                        // Bluetooth
                        String address =
                                data.getExtras().getString(DeviceListActivity.EXTRA_DEVICE_ADDRESS);
                        edit.putString(PREF_DEVICE_ADDRESS, address);
                        edit.apply();
                        mBtDeviceAddress = address;
                        startConnectionTimer();
                    } else if (data.getExtras().containsKey(UsbDeviceActivity.EXTRA_DEVICE_SERIAL)){
                        // USB
                        String serial =
                                data.getExtras().getString(UsbDeviceActivity.EXTRA_DEVICE_SERIAL);

                        edit.putString(PREF_DEVICE_USBSERIAL, serial);
                        edit.apply();
                        mUsbSerialNumber = serial;
                        startConnectionTimer();
                        mLogView.append("Using USB HW # " + serial + "\n");
                    }
                } else if (resultCode == Activity.RESULT_CANCELED) {
                    if (data != null) {
                        if (Objects.requireNonNull(data.getExtras()).containsKey(UsbDeviceActivity.EXTRA_DEVICE_SERIAL)) {
                            String error_code =
                                    data.getExtras().getString(UsbDeviceActivity.EXTRA_DEVICE_SERIAL);
                            mLogView.append("Using USB connection error : " + error_code + "\n");
                        }
                    }
                }
                break;
            case REQUEST_ENABLE_BT:
                // When the request to enable Bluetooth returns
                break;
            case REQUEST_SCREEN:
                setConnectionStatus(STATE_DISCONNECTED);
                break;
        }
    }

    void parseDatabase(){
        String ecuFile = "";
        SharedPreferences defaultPrefs = this.getSharedPreferences(DEFAULT_PREF_TAG, MODE_PRIVATE);
        if (defaultPrefs.contains(PREF_ECUZIPFILE)) {
            ecuFile = defaultPrefs.getString(PREF_ECUZIPFILE, "");
        }
        mStatusView.setText(getResources().getString(R.string.INDEXING_DB));
        new LoadDbTask().execute(ecuFile);
    }

    void updateEcuTypeListView(String ecuFile, String project){
        if (ecuFile == null || ecuFile.isEmpty()){
            mStatusView.setText(getResources().getString(R.string.DB_NOT_FOUND));
            return;
        }

        //mEcuDatabase.checkMissings();

        SharedPreferences defaultPrefs = getSharedPreferences(DEFAULT_PREF_TAG, MODE_PRIVATE);
        SharedPreferences.Editor edit = defaultPrefs.edit();
        edit.putString(PREF_ECUZIPFILE, ecuFile);
        edit.apply();

        mEcuFilePath = ecuFile;
        ArrayAdapter<String> adapter;
        ArrayList<String> adapterList = mEcuDatabase.getEcuByFunctionsAndType(project);
        Collections.sort(adapterList);
        if (adapterList.isEmpty())
            return;
        adapter = new ArrayAdapter<>(this,
                android.R.layout.simple_list_item_1,
                adapterList);

        mEcuListView.setAdapter(adapter);
    }

    public class LoadDbTask extends AsyncTask<String, Void, String> {
        private String error;

        @Override
        protected String doInBackground(String... params) {
            String ecuFile = params[0];
            error = "";
            try {
                String appDir = getApplicationContext().getFilesDir().getAbsolutePath();
                ecuFile = mEcuDatabase.loadDatabase(ecuFile, appDir);
            } catch (EcuDatabase.DatabaseException e){
                error = e.getMessage();
                return "";
            }
            return ecuFile;
        }

        @Override
        protected void onPostExecute(String ecuFile) {
            SharedPreferences defaultPrefs = getSharedPreferences(DEFAULT_PREF_TAG, MODE_PRIVATE);
            mCurrentProject = defaultPrefs.getString(PREF_PROJECT, "");
            updateEcuTypeListView(ecuFile, mCurrentProject);
            mStatusView.setText("ECU-TWEAKER");
            if (!error.isEmpty()){
                mLogView.append("Database exception : " + error + "\n");
            }
        }
    }

    private void displayHelp(){
        Spanned message = Html.fromHtml(getResources().getString(R.string.DEMO_MESSAGE));
        AlertDialog alertDialog = new AlertDialog.Builder(MainActivity.this).create();
        alertDialog.setTitle(getResources().getString(R.string.INFORMATION));
        alertDialog.setMessage(message);
        alertDialog.setButton(AlertDialog.BUTTON_NEUTRAL, getResources().getString(R.string.OK),
                (dialog, which) -> dialog.dismiss());
        alertDialog.show();
    }

    private void chooseProject(){
        if (!mEcuDatabase.isLoaded())
            return;
        AlertDialog.Builder builder = new AlertDialog.Builder(this);
        builder.setTitle(getResources().getString(R.string.CHOOSE_PROJECT));

        /*
         * Clean view
         */
        ArrayList<String> ecuNames = new ArrayList<>();
        ArrayAdapter<String> adapter = new ArrayAdapter<String>(this,
                android.R.layout.simple_list_item_1,
                ecuNames);
        mSpecificEcuListView.setAdapter(adapter);

        final String[] projects = mEcuDatabase.getModels();

        Arrays.sort(projects);
        builder.setItems(projects, new DialogInterface.OnClickListener() {
            @Override
            public void onClick(DialogInterface dialog, int which) {
                mCurrentProject = mEcuDatabase.getProjectFromModel(projects[which]);
                SharedPreferences defaultPrefs = getSharedPreferences(DEFAULT_PREF_TAG, MODE_PRIVATE);
                SharedPreferences.Editor edit = defaultPrefs.edit();
                edit.putString(PREF_PROJECT, mCurrentProject);
                edit.apply();
                updateEcuTypeListView(mEcuFilePath, mCurrentProject);
            }
        });

        AlertDialog dialog = builder.create();
        dialog.show();
    }

    private void handleElmResult(String elmMessage){
        String[] results = elmMessage.split(";");
        if (results.length < 2){
            return;
        }
        if (results[1].isEmpty() || results[0].substring(0,2).equalsIgnoreCase("AT")){
            return;
        }

        String ecuResponse = results[1].replace(" ", "");
        mLogView.append("> " + results[0] + " : " + results[1] + "\n");

        /*
         * Old method auto identification
         */
        if (ecuResponse.length() > 39 && ecuResponse.startsWith("6180")) {
            // We get our data, stop scanning
            mObdDevice.clearMessages();
            stopProgressDialog();

            // Search best ECU file
            String supplier = new String(Ecu.hexStringToByteArray(ecuResponse.substring(16, 22)));
            String soft_version = ecuResponse.substring(32, 36);
            String version = ecuResponse.substring(36, 40);
            String diag_version_string = ecuResponse.substring(14, 16);
            int diag_version = Integer.parseInt(diag_version_string, 16);
            mViewDiagVersion.setText(diag_version_string);
            mViewSupplier.setText(supplier);
            mViewSoft.setText(version);
            mViewVersion.setText(soft_version);
            mLogView.append(getResources().getString(R.string.ECU_FOUND) + " : " +
                    getResources().getString(R.string.SUPPLIER_VERSION) + " " + supplier +
                    getResources().getString(R.string.DIAG_VERSION) + " : "
                    + diag_version_string + " " +getResources().getString(R.string.VERSION)
                    + " : " + version
                    + " " + getResources().getString(R.string.SOFT_VERSION) + " : "
                    + soft_version + "\n");

            EcuDatabase.EcuInfo ecuInfo = mEcuDatabase.identifyOldEcu(mCurrentEcuAddressId,
                    supplier, soft_version, version, diag_version);

            if (ecuInfo != null) {
                ArrayList<String> ecuNames = new ArrayList<>();
                ecuNames.add(ecuInfo.ecuName);
                Collections.sort(ecuNames);
                ArrayAdapter<String> adapter;
                adapter = new ArrayAdapter<>(this,
                        android.R.layout.simple_list_item_1,
                        ecuNames);
                mSpecificEcuListView.setAdapter(adapter);
                if (!ecuInfo.exact_match) {
                    mSpecificEcuListView.setBackgroundColor(Color.RED);
                    mLogView.append(getResources().getString(R.string.ECU_PART_MATCH) + " "
                            + ecuInfo.ecuName + "\n");
                } else {
                    mSpecificEcuListView.setBackgroundColor(Color.GREEN);
                    mLogView.append(getResources().getString(R.string.ECU_MATCH) + " " + ecuInfo.ecuName + "\n");
                }
            }
        }

        /*
         * New method auto identification
         */
        if (ecuResponse.length() > 5) {
            if (ecuResponse.startsWith("62F1A0")) {
                mEcuIdentifierNew.diag_version = ecuResponse.substring(6);
                mViewDiagVersion.setText(mEcuIdentifierNew.diag_version);
            }
            if (ecuResponse.startsWith("62F18A")) {
                mEcuIdentifierNew.supplier = ecuResponse.substring(6);
                mViewSupplier.setText(mEcuIdentifierNew.supplier);
            }
            if (ecuResponse.startsWith("62F194")) {
                mEcuIdentifierNew.version = ecuResponse.substring(6);
                mViewSoft.setText(mEcuIdentifierNew.version);
            }
            if (ecuResponse.startsWith("62F195")) {
                mEcuIdentifierNew.soft_version = ecuResponse.substring(6);
                mViewVersion.setText(mEcuIdentifierNew.soft_version);
            }
        }

        // If we get all ECU info, search in DB
        if (mEcuIdentifierNew.isFullyFilled()){
            mEcuIdentifierNew.reInit(-1);
            ArrayList<EcuDatabase.EcuInfo> ecuInfos = mEcuDatabase.identifyNewEcu(mEcuIdentifierNew);
            ArrayList<String> ecuNames = new ArrayList<>();
            boolean isExact = false;
            for (EcuDatabase.EcuInfo ecuInfo : ecuInfos) {
                ecuNames.add(ecuInfo.ecuName);
                if (ecuInfo.exact_match)
                    isExact = true;
            }
            Collections.sort(ecuNames);
            ArrayAdapter<String> adapter;
            adapter = new ArrayAdapter<>(this,
                    android.R.layout.simple_list_item_1,
                    ecuNames);
            mSpecificEcuListView.setAdapter(adapter);
            if (isExact){
                mSpecificEcuListView.setBackgroundColor(Color.GREEN);
            } else {
                mSpecificEcuListView.setBackgroundColor(Color.RED);
            }
        }
    }

    private static class messageHandler extends Handler {
        private final MainActivity activity;
        messageHandler(MainActivity ac){
            activity = ac;
        }

        public void handleMessage(Message msg) {
            switch (msg.what) {
                case MESSAGE_STATE_CHANGE:
                    if (BuildConfig.DEBUG)
                        Log.i(TAG, "MESSAGE_STATE_CHANGE: " + msg.arg1);
                    switch (msg.arg1) {
                        case STATE_CONNECTED:
                            activity.setConnectionStatus(STATE_CONNECTED);
                            break;
                        case STATE_CONNECTING:
                            activity.setConnectionStatus(STATE_CONNECTING);
                            break;
                        case STATE_NONE:
                        case STATE_DISCONNECTED:
                            activity.setConnectionStatus(STATE_DISCONNECTED);
                            activity.stopProgressDialog();
                            break;
                    }
                    break;
                case MESSAGE_READ:
                    byte[] m = (byte[]) msg.obj;
                    String readMessage = new String(m, 0, msg.arg1);
                    try {
                        activity.handleElmResult(readMessage);
                    } catch (Exception e){
                        AlertDialog.Builder dlgAlert  = new AlertDialog.Builder(activity);
                        dlgAlert.setMessage(e.getMessage());
                        dlgAlert.setTitle("Exception caught");
                        dlgAlert.setPositiveButton("OK", null);
                        dlgAlert.create().show();
                        activity.mLogView.append("Exception : " + e.getMessage() + "\n");
                    }
                    break;
                case MESSAGE_DEVICE_NAME:
                    break;
                case MESSAGE_TOAST:
                    Toast.makeText(activity.getApplicationContext(), msg.getData().getString(TOAST),
                            Toast.LENGTH_SHORT).show();
                    break;
                case MESSAGE_LOG:
                    activity.mLogView.append(activity.getResources().getString(R.string.BT_MANAGER_MESSAGE) + " : "
                            + msg.getData().getString(TOAST) + "\n");
                    break;
                case MESSAGE_QUEUE_STATE:
                    int queue_len = msg.arg1;
                    if (queue_len == 0){
                        activity.stopProgressDialog();
                    }
                    break;
            }
        }
    }

    void stopProgressDialog(){
        if (mScanProgressDialog != null) {
            mScanProgressDialog.dismiss();
        }
    }

    void setConnectionStatus(int c){
        //mScanButton.setEnabled(c == STATE_CONNECTED ? true : false);
        if (c == STATE_CONNECTED){
            mBtIconImage.setColorFilter(Color.GREEN);
            mBtIconImage.setImageResource(R.drawable.ic_link_ok);
        } else if (c == STATE_DISCONNECTED){
            mBtIconImage.setColorFilter(Color.RED);
            mBtIconImage.setImageResource(R.drawable.ic_link_nok);
        } else if (c == STATE_CONNECTING){
            mBtIconImage.setColorFilter(Color.GRAY);
            mBtIconImage.setImageResource(R.drawable.ic_link_ok);
        }
    }

    private void sendCmd(String cmd) {
        // Check that we're actually connected before trying anything
        if (!isChatConnected()) {
            return;
        }

        // Send command
        mObdDevice.write(cmd);
    }

    private boolean isChatConnected(){
        return mObdDevice != null && (mObdDevice.getState() == STATE_CONNECTED);
    }

    private boolean isChatConnecting(){
        return mObdDevice != null && (mObdDevice.getState() == STATE_CONNECTING);
    }

    protected String getTimeStamp() {
        return "[" + new SimpleDateFormat("dd-MM-hh:mm:ss").format(new Date()) + "] ";
    }

    public void copyLogs() throws IOException {
        if (mObdDevice != null)
            mObdDevice.flushLogs();

        if (ContextCompat.checkSelfPermission(this,
                Manifest.permission.WRITE_EXTERNAL_STORAGE)
                == PackageManager.PERMISSION_GRANTED) {
            String logSrc = getApplicationContext().getFilesDir().getAbsolutePath() + "/log.txt";
            String logFilename = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS) + "/logs_" + getTimeStamp() + ".txt";
            File src = new File(logSrc);
            File dst = new File(logFilename);
            try (InputStream in = new FileInputStream(src)) {
                try (OutputStream out = new FileOutputStream(dst)) {
                    // Transfer bytes from in to out
                    byte[] buf = new byte[1024];
                    int len;
                    while ((len = in.read(buf)) > 0) {
                        out.write(buf, 0, len);
                    }
                }
                Toast.makeText(this,
                        "Logs copied to your Download directory",
                        Toast.LENGTH_SHORT).show();
            } catch (IOException e) {
                mLogView.append("Error copying logs : " + e.getMessage() + "\n");
            }
        } else {
            Toast.makeText(this,
                    "You need write storage permission",
                    Toast.LENGTH_SHORT).show();
        }
    }
}
