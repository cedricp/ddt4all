package org.quark.dr.canapp;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Color;
import android.os.Bundle;
import android.os.Handler;
import android.os.Message;
import android.text.Html;
import android.text.Spanned;
import android.text.method.ScrollingMovementMethod;
import android.util.Pair;
import androidx.appcompat.app.AppCompatActivity;
import android.util.Log;
import android.util.TypedValue;
import android.view.Gravity;
import android.view.LayoutInflater;
import android.view.View;
import android.view.Menu;
import android.view.MenuItem;
import android.view.ViewGroup;
import android.widget.AdapterView;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.CheckBox;
import android.widget.EditText;
import android.widget.FrameLayout;
import android.widget.ImageButton;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.RelativeLayout;
import android.widget.ScrollView;
import android.widget.SeekBar;
import android.widget.Spinner;
import android.widget.TextView;
import android.widget.Toast;

import org.quark.dr.ecu.Ecu;
import org.quark.dr.ecu.EcuDatabase;
import org.quark.dr.ecu.IsoTPDecode;
import org.quark.dr.ecu.Layout;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;

import static org.quark.dr.canapp.ElmBluetooth.STATE_CONNECTED;
import static org.quark.dr.canapp.ElmBluetooth.STATE_CONNECTING;
import static org.quark.dr.canapp.ElmBluetooth.STATE_DISCONNECTED;
import static org.quark.dr.canapp.ElmBluetooth.STATE_NONE;
import static org.quark.dr.canapp.MainActivity.PREF_FONT_SCALE;
import static org.quark.dr.canapp.MainActivity.PREF_GLOBAL_SCALE;
import static org.quark.dr.canapp.MainActivity.PREF_SOFTFLOW;
import static org.quark.dr.ecu.Ecu.hexStringToByteArray;

public class ScreenActivity extends AppCompatActivity {
    private static final String TAG = "org.quark.dr.ecutweaker";
    private ScrollView m_scrollView;
    private RelativeLayout m_layoutView;
    private Ecu m_ecu;
    private Layout m_currentLayoutData;
    private Layout.ScreenData m_currentScreenData;
    private ImageButton m_reloadButton;
    private ImageView m_btIconStatus, m_btCommStatus;
    private TextView m_logView;
    private String m_currentScreenName;
    private String m_currentEcuName;
    private String m_currentDtcRequestName, m_currentDtcRequestBytes, m_clearDTCCommand;
    private boolean m_autoReload;
    private EcuDatabase m_ecuDatabase;

    private HashMap<String, EditText> m_editTextViews;
    private HashMap<String, EditText> m_displayViews;
    private HashMap<String, Spinner> m_spinnerViews;
    private HashMap<String, View> m_buttonsViews;
    private HashMap<View, String> m_buttonsCommand;
    private HashMap<String, ArrayList<Layout.InputData>> m_requestsInputs;
    private Set<String> m_displaysRequestSet, m_startRequestSet;

    private ElmBase mChatService = null;
    private Handler mHandler = null;

    private int mCanTimeOut;
    private int mFontSizeOverride;

    // Intent request codes
    private static final int    REQUEST_CONNECT_DEVICE = 1;
    private static final int    REQUEST_ENABLE_BT      = 3;

    public static final int     MESSAGE_STATE_CHANGE    = 1;
    public static final int     MESSAGE_READ            = 2;
    public static final int     MESSAGE_WRITE           = 3;
    public static final int     MESSAGE_DEVICE_NAME     = 4;
    public static final int     MESSAGE_TOAST           = 5;
    public static final int     MESSAGE_QUEUE_STATE     = 6;
    public static final int     MESSAGE_LOG             = 7;
    public static final String  DEVICE_NAME = "device_name";
    public static final String  TOAST       = "toast";
    private String              mConnectedDeviceName = null;
    private float               mGlobalScale;
    private long                mLastSDSTime;
    private boolean             mDemoMode, mSoftFlowControl;

    public float convertToPixel(float val){
        return (val / 8.0f) * mGlobalScale;
    }

    public float convertFontToPixel(int val){
        return val * 2 * ((float)mFontSizeOverride / 100.0f) * mGlobalScale;
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_screen);
        initialize(savedInstanceState);
    }

    private void initialize(Bundle savedInstanceState) {
        mCanTimeOut = 0;
        //mDemoMode = true;
        mDemoMode = false;
        String ecuFile = "";
        String ecuHref = "";
        m_autoReload = false;
        SharedPreferences defaultPrefs = this.getSharedPreferences(MainActivity.DEFAULT_PREF_TAG,
                MODE_PRIVATE);

        String globalScalePref = defaultPrefs.getString(PREF_GLOBAL_SCALE, "1.3");
        mFontSizeOverride = defaultPrefs.getInt(PREF_FONT_SCALE, 100);
        mGlobalScale = Float.parseFloat(globalScalePref);
        mSoftFlowControl = defaultPrefs.getBoolean(PREF_SOFTFLOW, false);

        mLastSDSTime = 0;
        int linkMode = MainActivity.LINK_WIFI;

        Bundle b = getIntent().getExtras();
        if (b != null) {
            ecuFile = b.getString("ecuFile");
            ecuHref = b.getString("ecuRef");
            if (b.containsKey("deviceAddress")){
                String m_deviceAddressPref = b.getString("deviceAddress");
            }
            //mDemoMode =  ! b.getBoolean("licenseOk");
            linkMode = b.getInt("linkMode", MainActivity.LINK_WIFI);
        } else if (savedInstanceState != null && savedInstanceState.containsKey("ecu_name")){
            ecuFile = savedInstanceState.getString("ecu_name");
        }

        m_reloadButton = findViewById(R.id.reloadButton);
        m_btIconStatus = findViewById(R.id.iconBt);
        ImageButton m_screenButton = findViewById(R.id.screenButton);
        m_btCommStatus = findViewById(R.id.bt_comm);
        ImageButton m_dtcButton = findViewById(R.id.dtcButton);
        ImageButton m_dtcClearButton = findViewById(R.id.dtcClearButton);
        ImageButton settingsButton = findViewById(R.id.settingsButton);
        settingsButton.setOnClickListener(v -> {
            LayoutInflater inflater= LayoutInflater.from(ScreenActivity.this);
            View view = inflater.inflate(R.layout.can_settings, null);
            ArrayList<String> sdsList = new ArrayList<>(m_ecu.getSdsrequests().keySet());

            AlertDialog.Builder alertDialog = new AlertDialog.Builder(ScreenActivity.this);
            alertDialog.setTitle("Settings");
            alertDialog.setView(view);
            AlertDialog alert = alertDialog.create();
            CheckBox softflowcheckbox = view.findViewById(R.id.checkBoxSFC);
            softflowcheckbox.setChecked(mSoftFlowControl);
            softflowcheckbox.setOnCheckedChangeListener((btn, b1) -> mSoftFlowControl = b1);
            SeekBar canSeekBar = view.findViewById(R.id.canTimeoutSeekBar);
            canSeekBar.setProgress(mCanTimeOut);
            Spinner sdsSpinner = view.findViewById(R.id.sdsSpinner);
            ArrayAdapter<String> dataAdapter = new ArrayAdapter<>(ScreenActivity.this,
                    android.R.layout.simple_list_item_1, sdsList);
            sdsSpinner.setAdapter(dataAdapter);
            sdsSpinner.setOnItemSelectedListener(new Spinner.OnItemSelectedListener(){
                @Override
                public void onItemSelected(AdapterView<?> parent, View view, int position, long id) {
                    String sdsname = ((TextView) view).getText().toString();
                    m_ecu.setDefautSDS(sdsname);
                    m_logView.append("Defaut diag session switched to " + m_ecu.getDefaultSDS() + "\n");
                }
                @Override
                public void onNothingSelected(AdapterView<?> parent){

                }
            });

            SeekBar fontSeekBar = view.findViewById(R.id.fontSizeBar);
            fontSeekBar.setProgress(mFontSizeOverride);
            fontSeekBar.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
                @Override
                public void onProgressChanged(SeekBar seekBar, int progress, boolean fromUser) {
                    mFontSizeOverride = progress;
                    if (mFontSizeOverride < 20)
                        mFontSizeOverride = 20;
                }

                @Override
                public void onStartTrackingTouch(SeekBar seekBar) {

                }

                @Override
                public void onStopTrackingTouch(SeekBar seekBar) {

                }
            });

            final TextView canTimeoutReport = view.findViewById(R.id.canTimeOutReport);
            canSeekBar.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
                @Override
                public void onProgressChanged(SeekBar seekBar, int progress, boolean fromUser) {
                    mCanTimeOut = progress;
                    canTimeoutReport.setText(String.valueOf(progress));
                }

                @Override
                public void onStartTrackingTouch(SeekBar seekBar) {

                }

                @Override
                public void onStopTrackingTouch(SeekBar seekBar) {

                }
            });
            alert.setButton(AlertDialog.BUTTON_POSITIVE,getResources().
                            getString(R.string.OK),
                    (dialog, which) -> {
                        applySettings();
                        drawScreen(m_currentScreenName);
                    });
            alert.show();
        });

        m_dtcButton.setOnClickListener(v -> {
            if (m_autoReload)
                stopAutoReload();
            readDTC();
        });

        m_dtcClearButton.setOnClickListener(v -> {
            if (m_autoReload)
                stopAutoReload();
            clearDTC();
        });

        m_reloadButton.setOnLongClickListener(v -> {
            if (!isChatConnected()){
                connectDevice();
                return true;
            }
            m_autoReload = !m_autoReload;
            if (m_autoReload){
                m_reloadButton.setColorFilter(Color.GREEN);
            } else {
                stopAutoReload();
            }
            updateDisplays();
            return true;
        });

        m_reloadButton.setOnClickListener(v -> {
            if (!isChatConnected()){
                connectDevice();
                Toast.makeText(getApplicationContext(),
                        getResources().getString(R.string.not_connected),
                        Toast.LENGTH_LONG).show();
                return;
            }

            if (m_autoReload)
                stopAutoReload();
            updateDisplays();
        });

        m_screenButton.setOnClickListener(v -> {
            if (m_autoReload)
                stopAutoReload();
            chooseCategory();
        });

        Button zoomInButton = findViewById(R.id.zoom_in);
        zoomInButton.setOnClickListener(v -> {
            mGlobalScale += 0.1f;
            drawScreen(m_currentScreenName);
        });

        Button zoomOutButton = findViewById(R.id.zoom_out);
        zoomOutButton.setOnClickListener(v -> {
            mGlobalScale -= 0.1f;
            if (mGlobalScale < 0.3f)
                mGlobalScale = 0.3f;
            drawScreen(m_currentScreenName);
        });

        m_scrollView = this.findViewById(R.id.scrollView);
        m_layoutView = this.findViewById(R.id.mainLayout);
        m_logView = this.findViewById(R.id.logView);
        m_logView.setGravity(Gravity.BOTTOM);
        m_logView.setMovementMethod(new ScrollingMovementMethod());
        m_logView.setBackgroundResource(R.drawable.edittextroundgreen);
        m_btIconStatus.setColorFilter(Color.RED);
        m_btIconStatus.setImageResource(R.drawable.ic_link_nok);
        m_logView.setTextIsSelectable(true);

        mHandler = new messageHandler(this);
        mChatService = ElmBase.getSingleton();

        if (mChatService != null && mChatService.getDB() != null) {
            m_ecuDatabase = mChatService.getDB();
        } else {
            m_ecuDatabase = new EcuDatabase();
            Log.e(TAG, "?? No singleton database, continuing safely");
        }

        if (mChatService == null) {
            // In case singleton is lost...
            if (MainActivity.LINK_BLUETOOTH == linkMode) {
                mChatService = ElmBase.createBluetoothSingleton(mHandler,
                        getApplicationContext().getFilesDir().getAbsolutePath());
            } else {
                mChatService = ElmBase.createWifiSingleton(getApplicationContext(), mHandler,
                        getApplicationContext().getFilesDir().getAbsolutePath());
            }
        } else {
            mChatService.changeHandler(mHandler);
        }

        mChatService.setSoftFlowControl(mSoftFlowControl);

        if (!ecuFile.isEmpty()){
            openEcu(ecuFile, ecuHref);
        }

        connectDevice();

        if (savedInstanceState != null && savedInstanceState.containsKey("screen_name")){
            m_currentScreenName = savedInstanceState.getString("screen_name");
            drawScreen(m_currentScreenName);
        } else {
            chooseCategory();
        }
        m_logView.append("Default diag session : " + m_ecu.getDefaultSDS() + "\n");
    }

    void applySettings(){
        if(isChatConnected()){
            mChatService.setTimeOut(mCanTimeOut);
        }
        SharedPreferences defaultPrefs =
                this.getSharedPreferences(MainActivity.DEFAULT_PREF_TAG, MODE_PRIVATE);
        SharedPreferences.Editor edit = defaultPrefs.edit();
        edit.putInt(PREF_FONT_SCALE, mFontSizeOverride);
        edit.putBoolean(PREF_SOFTFLOW, mSoftFlowControl);
        edit.apply();
    }

    void stopAutoReload(){
        m_autoReload = false;
        m_reloadButton.clearColorFilter();
    }

    void openEcu(String ecuFile, String ecuName){
        String layoutFileName = ecuName + ".layout";

        String appDir = getApplicationContext().getFilesDir().getAbsolutePath();
        try {
            m_ecuDatabase.loadDatabase(ecuFile, appDir);
            String ecuJson = m_ecuDatabase.getZipFile(ecuName);
            String layoutJson = m_ecuDatabase.getZipFile(layoutFileName);

            m_ecu = new Ecu(ecuJson);
            m_currentLayoutData = new Layout(layoutJson);
            m_currentEcuName = ecuName;
        } catch (EcuDatabase.DatabaseException e){
            e.printStackTrace();
        }
    }

    @Override
    public void onSaveInstanceState(Bundle outState) {
        outState.putString("screen_name", m_currentScreenName);
        outState.putString("ecu_name", m_currentEcuName);
        super.onSaveInstanceState(outState);
    }

    void drawScreen(String screenName)
    {
        // In case the user clicked multiple times on zoom button
        // and there are messages pending
        mChatService.clearMessages();

        m_displayViews = new HashMap<>();
        m_editTextViews = new HashMap<>();
        m_spinnerViews = new HashMap<>();
        m_buttonsViews = new HashMap<>();
        m_buttonsCommand = new HashMap<>();
        m_requestsInputs = new HashMap<>();
        m_displaysRequestSet = new HashSet<>();
        m_startRequestSet =  new HashSet<>();

        if (m_currentLayoutData == null)
            return;

        m_currentScreenData = m_currentLayoutData.getScreen(screenName);
        if (m_currentScreenData == null)
            return;

        for (Pair<Integer, String> pair : m_currentScreenData.getPreSendData()){
            Ecu.EcuRequest request = m_ecu.getRequest(pair.second);
            // Skip start diagnostic session
            if (request.sentbytes.startsWith("10"))
                continue;
            m_startRequestSet.add(pair.second);
        }

        m_layoutView.removeAllViews();
        m_layoutView.setLayoutParams(new FrameLayout.LayoutParams(
                (int) convertToPixel(m_currentScreenData.m_width) + 80,
                (int) convertToPixel(m_currentScreenData.m_height) + 80));
        m_layoutView.setBackgroundColor(m_currentScreenData.m_color.get());

        for (Layout.LabelData labelData: m_currentScreenData.getLabels()) {
            if (labelData.text.toUpperCase().startsWith("::PIC:")){
                String gifName = labelData.text;

                gifName = gifName.replace("::pic:", "")
                        .replace("::PIC:", "")
                        .replace("\\", "/");
                String filenameu = "graphics/" + gifName + ".GIF";
                String filenamel = "graphics/" + gifName + ".gif";

                byte[] imageBytes = null;
                if (m_ecuDatabase.getZipFileSystem().fileExists(filenameu)){
                    imageBytes = m_ecuDatabase.getZipFileSystem().getZipFileAsBytes(filenameu);
                } else if (m_ecuDatabase.getZipFileSystem().fileExists(filenamel)){
                    imageBytes = m_ecuDatabase.getZipFileSystem().getZipFileAsBytes(filenamel);
                }

                if (imageBytes != null) {
                    ImageView imageView = new ImageView(this);
                    Bitmap bm = BitmapFactory.decodeByteArray(imageBytes, 0,
                            imageBytes.length);
                    imageView.setX(convertToPixel(labelData.rect.x));
                    imageView.setY(convertToPixel(labelData.rect.y));
                    int w = (int) convertToPixel(labelData.rect.w);
                    int h = (int) convertToPixel(labelData.rect.h);
                    LinearLayout.LayoutParams parms = new LinearLayout.LayoutParams(w, h);
                    imageView.setLayoutParams(parms);
                    imageView.setScaleType(ImageView.ScaleType.FIT_XY);
                    imageView.setImageBitmap(bm);
                    m_layoutView.addView(imageView);
                }
            } else {
                TextView textView = new TextView(this);
                textView.setX(convertToPixel(labelData.rect.x));
                textView.setY(convertToPixel(labelData.rect.y));
                textView.setWidth((int) convertToPixel(labelData.rect.w));
                textView.setHeight((int) convertToPixel(labelData.rect.h));
                textView.setText(labelData.text);
                textView.setBackgroundColor(labelData.color.get());
                textView.setTextColor(labelData.font.color.get());
                textView.setTextSize(TypedValue.COMPLEX_UNIT_PX,
                        convertFontToPixel(labelData.font.size));
                if (labelData.alignment == 2) {
                    textView.setGravity(Gravity.CENTER_HORIZONTAL);
                } else if (labelData.alignment == 1) {
                    textView.setGravity(Gravity.RIGHT);
                }
                m_layoutView.addView(textView);
            }
        }

        for (Layout.DisplayData displaydata : m_currentScreenData.getDisplays()){
            if (displaydata.width > 0) {
                TextView textView = new TextView(this);
                textView.setX(convertToPixel(displaydata.rect.x));
                textView.setY(convertToPixel(displaydata.rect.y));
                textView.setWidth((int) convertToPixel(displaydata.width));
                textView.setHeight((int) convertToPixel(displaydata.rect.h));
                textView.setText(displaydata.text);
                textView.setTextColor(displaydata.font.color.get());
                textView.setBackgroundColor(displaydata.color.get());
                textView.setTextSize(TypedValue.COMPLEX_UNIT_PX,
                        convertFontToPixel(displaydata.font.size));
                textView.setGravity(Gravity.LEFT | Gravity.CENTER_VERTICAL);
                m_layoutView.addView(textView);
            }

            EditText textEdit = new EditText(this);
            textEdit.setBackgroundResource(R.drawable.edittextroundgreen);
            textEdit.setX(convertToPixel(displaydata.rect.x + displaydata.width));
            textEdit.setY(convertToPixel(displaydata.rect.y));
            textEdit.setWidth((int) convertToPixel(displaydata.rect.w - displaydata.width));
            textEdit.setHeight((int) convertToPixel(displaydata.rect.h));
            textEdit.setTextSize(TypedValue.COMPLEX_UNIT_PX,
                    convertFontToPixel(displaydata.font.size));
            textEdit.setEnabled(false);
            textEdit.setText("---");
            textEdit.setPadding(3,3,3,3);
            textEdit.setBackgroundColor(displaydata.color.get());
            textEdit.setTextColor(displaydata.font.color.get());
            textEdit.setFocusable(false);
            m_displayViews.put(displaydata.text, textEdit);
            m_layoutView.addView(textEdit);
            m_displaysRequestSet.add(displaydata.request);
        }

        for (Layout.InputData inputdata: m_currentScreenData.getInputs()){
            if (inputdata.width > 0) {
                TextView textView = new TextView(this);
                textView.setX(convertToPixel(inputdata.rect.x));
                textView.setY(convertToPixel(inputdata.rect.y));
                textView.setWidth((int) convertToPixel(inputdata.width));
                textView.setHeight((int) convertToPixel(inputdata.rect.h));
                textView.setText(inputdata.text);
                textView.setTextColor(inputdata.font.color.get());
                textView.setBackgroundColor(inputdata.color.get());
                m_layoutView.addView(textView);
            }

            if (m_ecu.getData(inputdata.text).items.size() == 0) {
                EditText textEdit = new EditText(this);
                textEdit.setX(convertToPixel(inputdata.rect.x + inputdata.width));
                textEdit.setY(convertToPixel(inputdata.rect.y));
                textEdit.setWidth((int) convertToPixel(inputdata.rect.w - inputdata.width));
                textEdit.setHeight((int) convertToPixel(inputdata.rect.h));
                textEdit.setTextSize(TypedValue.COMPLEX_UNIT_PX,
                        convertFontToPixel(inputdata.font.size));
                textEdit.setPadding(3, 3, 3, 3);
                textEdit.setTextColor(inputdata.font.color.get());
                textEdit.setBackgroundColor(inputdata.color.get());
                textEdit.setSingleLine();
                textEdit.setBackgroundResource(R.drawable.edittextroundred);
                m_editTextViews.put(inputdata.text, textEdit);
                m_layoutView.addView(textEdit);
            } else {
                String[] items = new String[m_ecu.getData(inputdata.text).items.size()];
                int i = 0;
                for (String item : m_ecu.getData(inputdata.text).items.keySet()){
                    items[i++] = item;
                }
                Arrays.sort(items);
                CustomAdapter dataAdapter = new CustomAdapter(this,
                        android.R.layout.simple_spinner_item, items);

                Spinner spinner = new Spinner(this);
                spinner.setX(convertToPixel(inputdata.rect.x + inputdata.width));
                spinner.setY(convertToPixel(inputdata.rect.y) - 5);
                ViewGroup.LayoutParams params = new ViewGroup.LayoutParams(
                        ((int) convertToPixel(inputdata.rect.w - inputdata.width)),
                        (int) convertToPixel(inputdata.rect.h) + 5);
                spinner.setLayoutParams(params);
                spinner.setBackgroundColor(inputdata.color.get());
                spinner.setBackgroundResource(R.drawable.spinnerround);
                dataAdapter.setSpinnerTextSize((int)convertFontToPixel(inputdata.font.size));
                dataAdapter.setSpinnerTextColor(inputdata.font.color.get());
                spinner.setAdapter(dataAdapter);
                m_spinnerViews.put(inputdata.text, spinner);
                m_layoutView.addView(spinner);
            }
            if (!m_requestsInputs.containsKey(inputdata.request)){
                m_requestsInputs.put(inputdata.request, new ArrayList<>());
            }
            ArrayList<Layout.InputData> tmp = m_requestsInputs.get(inputdata.request);
            tmp.add(inputdata);
        }

        for (Layout.ButtonData buttondata: m_currentScreenData.getButtons()) {
            if (buttondata.text.toUpperCase().startsWith("::BTN:")){
                String gifName = buttondata.text;

                gifName = gifName.replace("::BTN:|", "")
                        .replace("::btn:|", "")
                        .replace("\\", "/");
                String filenameu = "graphics/" + gifName + ".GIF";
                String filenamel = "graphics/" + gifName + ".gif";

                byte[] imageBytes = null;
                if (m_ecuDatabase.getZipFileSystem().fileExists(filenameu)) {
                    imageBytes = m_ecuDatabase.getZipFileSystem().getZipFileAsBytes(filenameu);
                } else if (m_ecuDatabase.getZipFileSystem().fileExists(filenamel)) {
                    imageBytes = m_ecuDatabase.getZipFileSystem().getZipFileAsBytes(filenamel);
                } else {
                    System.out.println("++ Not found " + filenameu);
                }

                if (imageBytes != null) {
                    ImageButton buttonImageView = new ImageButton(this);
                    Bitmap bm = BitmapFactory.decodeByteArray(imageBytes, 0,
                            imageBytes.length);
                    buttonImageView.setX(convertToPixel(buttondata.rect.x));
                    buttonImageView.setY(convertToPixel(buttondata.rect.y));
                    int w = (int) convertToPixel(buttondata.rect.w);
                    int h = (int) convertToPixel(buttondata.rect.h);
                    LinearLayout.LayoutParams parms = new LinearLayout.LayoutParams(w, h);
                    buttonImageView.setLayoutParams(parms);
                    buttonImageView.setScaleType(ImageView.ScaleType.FIT_XY);
                    buttonImageView.setImageBitmap(bm);
                    buttonImageView.setOnClickListener(buttonClickListener);
                    m_buttonsCommand.put(buttonImageView, buttondata.uniqueName);
                    m_layoutView.addView(buttonImageView);
                    m_buttonsViews.put(buttondata.uniqueName, buttonImageView);
                }
            } else {

                Button buttonView = new Button(this);
                buttonView.setX(convertToPixel(buttondata.rect.x));
                buttonView.setY(convertToPixel(buttondata.rect.y) - 15);
                RelativeLayout.LayoutParams params = new RelativeLayout.LayoutParams(
                        (int) convertToPixel(buttondata.rect.w),
                        (int) convertToPixel(buttondata.rect.h) + 15);
                buttonView.setLayoutParams(params);
                buttonView.setPadding(0, 0, 0, 0);
                buttonView.setText(buttondata.text);
                buttonView.setTextSize(TypedValue.COMPLEX_UNIT_PX,
                        convertFontToPixel(buttondata.font.size));
                buttonView.setOnClickListener(buttonClickListener);
                m_buttonsCommand.put(buttonView, buttondata.uniqueName);
                m_layoutView.addView(buttonView);
                m_buttonsViews.put(buttondata.uniqueName, buttonView);
            }
        }

        m_scrollView.requestLayout();
        updateDisplays();
        // test data
        //updateScreen("222130", "62213021000115293D55");
    }

    void updateDisplays(){
        if (!isChatConnected()) {
            setConnectionStatus(STATE_DISCONNECTED);
            return;
        }

        if (m_currentScreenData == null){
            // No screen defined yet
            return;
        }

        // If autoupdate, we don't want to send diag session every time
        if (System.currentTimeMillis() - mLastSDSTime > 3000) {
            sendCmd(m_ecu.getDefaultSDS());
            mLastSDSTime = System.currentTimeMillis();
        }

        // Enable tester-present frame periodically
        mChatService.setSessionActive(true);

        // screen pre-send data
        for (Pair<Integer, String> pair : m_currentScreenData.getPreSendData()){
            if (pair.first > 0)
                sendDelay(pair.first);
            Ecu.EcuRequest request = m_ecu.getRequest(pair.second);
            sendCmd(request.sentbytes);
        }

        if (m_displaysRequestSet == null)
            return;

        // Display requests send
        for(String requestname : m_displaysRequestSet){
            Ecu.EcuRequest request = m_ecu.getRequest(requestname);
            if (BuildConfig.DEBUG)
                Log.i(TAG, "Managing request : " + requestname);
            if (request == null){
                if (BuildConfig.DEBUG)
                    Log.i(TAG, "Cannot find request " + requestname);
            }
            if (BuildConfig.DEBUG)
                Log.i(TAG, "Send bytes " + Objects.requireNonNull(request).sentbytes);

            sendCmd(Objects.requireNonNull(request).sentbytes);
        }
    }

    private void updateScreen(String req, String response){
        if (req.isEmpty() && response.isEmpty()) {
            return;
        }

        if (!isChatConnected()){
            connectDevice();
        }

        if (response.length() < 4){
            return;
        }

        int responseHeader, requestHeader;
        try {
            responseHeader = Integer.parseInt(response.substring(0, 2), 16);
            requestHeader = Integer.parseInt(req.substring(0, 2), 16);
        } catch (Exception e){
            m_logView.append("Cannot decode service ID of " + response + "/" + req + "\n");
            return;
        }

        // Check response is ok
        if (requestHeader + 0x40 != responseHeader) {
            m_logView.append(getResources().getString(R.string.BAD_RESPONSE)
                    + " (" + responseHeader + ") " + getResources().getString(R.string.TO_REQUEST) +
                    " : " + requestHeader + "\n");
            return;
        }

        Set<String> globalRequestSet = new HashSet<>();
        globalRequestSet.addAll(m_displaysRequestSet);
        globalRequestSet.addAll(m_startRequestSet);

        for (String requestname : globalRequestSet) {
            Ecu.EcuRequest request = m_ecu.getRequest(requestname);
            if (BuildConfig.DEBUG)
                Log.i(TAG, "Managing request : " + requestname);
            if (request == null) {
                if (BuildConfig.DEBUG)
                    Log.i(TAG, "Cannot find request " + requestname);
                continue;
            }

            if (request.sentbytes.equals(req)) {
                HashMap<String, Pair<String, String>> mapValues;
                try {
                    byte[] bytes = hexStringToByteArray(response);
                    mapValues = m_ecu.getRequestValuesWithUnit(bytes, requestname);
                } catch (Exception e) {
                    m_logView.append("Cannot decode request " + requestname + "\n");
                    m_logView.append("Exception : " + e + "\n");
                    continue;
                }

                for (String key : mapValues.keySet()) {
                    if (m_displayViews.containsKey(key)) {
                        m_displayViews.get(key).setText(mapValues.get(key).first
                                + " " + mapValues.get(key).second);
                    }
                    if (m_editTextViews.containsKey(key)) {
                        m_editTextViews.get(key).setText(mapValues.get(key).first);
                    }
                    if (m_spinnerViews.containsKey(key)) {
                        Spinner spinner = m_spinnerViews.get(key);
                        spinner.setSelection(((CustomAdapter) spinner.getAdapter())
                                .getPosition(mapValues.get(key).first));
                    }
                }
            }
        }
    }

    private final View.OnClickListener buttonClickListener = new View.OnClickListener() {
        @Override
        public void onClick(View v) {
            if (mDemoMode){
                return;
            }
            if (! m_buttonsCommand.containsKey(v))
                return;
            String uniqueName = m_buttonsCommand.get(v);
            exectuteButtonCommands(uniqueName);
        }
    };

    void exectuteButtonCommands(String buttonUniqueName){
        Layout.ButtonData buttonData = m_currentScreenData.getButtonData(buttonUniqueName);
        if (buttonData == null)
            return;

        ArrayList<Pair<Integer, String>> commands = new ArrayList<>();
        for(Pair<Integer, String> sendData: buttonData.sendData){
            Integer delay = sendData.first;
            Ecu.EcuRequest request = m_ecu.getRequest(sendData.second);
            if (request == null){
                if (BuildConfig.DEBUG)
                    Log.d(TAG, "Cannot find request " + sendData.second);
                return;
            }

            if (!m_requestsInputs.containsKey(sendData.second)){
                commands.add(new Pair<>(delay, request.sentbytes));
                if (BuildConfig.DEBUG)
                    Log.d(TAG, ">>>>>>>>>>> Computed (no data) " + request.sentbytes);
                continue;
            }

            HashMap<String, Object> inputBuilder = new HashMap<>();

            ArrayList<Layout.InputData> inputs = m_requestsInputs.get(sendData.second);
            for (Layout.InputData input : inputs){
                if (m_editTextViews.containsKey(input.text)){
                    EditText editText = m_editTextViews.get(input.text);
                    String currentText = editText.getText().toString();
                    if (request.sendbyte_dataitems.containsKey(input.text)){
                        Ecu.EcuData ecuData = m_ecu.getData(input.text);
                        if (!ecuData.bytesascii) {
                            if (ecuData.scaled) {
                                if (!currentText.matches("[-+]?[0-9]*\\.?[0-9]+")) {
                                    Toast.makeText(getApplicationContext(),
                                            getResources().getString(R.string.INVALID_VALUE),
                                            Toast.LENGTH_LONG).show();
                                    return;
                                }
                            } else {
                                if (!IsoTPDecode.isHexadecimal(currentText)) {
                                    Toast.makeText(getApplicationContext(),
                                            getResources().getString(R.string.INVALID_VALUE),
                                            Toast.LENGTH_LONG).show();
                                    return;
                                }
                            }
                        }
                    } else {
                        Log.e("canapp", "Cannot find data " + input.text);
                    }
                    inputBuilder.put(input.text, currentText);
                }

                if (m_spinnerViews.containsKey(input.text)){
                    Spinner spinner = m_spinnerViews.get(input.text);
                    String currentText = spinner.getSelectedItem().toString();
                    inputBuilder.put(input.text, currentText);
                }
            }
            byte[] builtStream;
            try {
                builtStream = m_ecu.setRequestValues(sendData.second, inputBuilder);
            } catch (Exception e) {
                e.printStackTrace();
                Toast.makeText(getApplicationContext(),
                        getResources().getString(R.string.FRAME_COMPUTE_FAILED),
                        Toast.LENGTH_LONG).show();
                return;
            }
            if (BuildConfig.DEBUG)
                Log.d(TAG,getResources().getString(R.string.COMPUTED_FRAME)
                        + " : " + Ecu.byteArrayToHex(builtStream));
            commands.add(new Pair<>(delay, Ecu.byteArrayToHex(builtStream)));
        }

        for (Pair<Integer, String> command : commands){
            if (command.first > 0)
                sendDelay(command.first);
            sendCmd(command.second);
        }
    }

    @Override
    public boolean onCreateOptionsMenu(Menu menu) {
        // Inflate the menu; this adds items to the action bar if it is present.
        getMenuInflater().inflate(R.menu.menu_main, menu);
        return true;
    }

    @Override
    public boolean onOptionsItemSelected(MenuItem item) {
        // Handle action bar item clicks here. The action bar will
        // automatically handle clicks on the Home/Up button, so long
        // as you specify a parent activity in AndroidManifest.xml.
        int id = item.getItemId();
        if (id == R.id.action_settings) {
            return true;
        }

        return super.onOptionsItemSelected(item);
    }

    @Override
    public void onActivityResult(int requestCode, int resultCode, Intent data) {
        switch (requestCode) {
            case REQUEST_CONNECT_DEVICE:
                // When DeviceListActivity returns with a device to connect
                if (resultCode == Activity.RESULT_OK) {
                    connectDevice();
                }
                break;
            case REQUEST_ENABLE_BT:
                // When the request to enable Bluetooth returns
                if (resultCode == Activity.RESULT_OK) {
                }
                break;
        }
    }

    @Override
    public void onDestroy()
    {
        Log.e(TAG, "+ ON DESTROY +");
        stopAutoReload();
        super.onDestroy();
    }

    @Override
    public void onStop()
    {
        SharedPreferences defaultPrefs =
                this.getSharedPreferences(MainActivity.DEFAULT_PREF_TAG, MODE_PRIVATE);
        SharedPreferences.Editor edit = defaultPrefs.edit();
        edit.putString(PREF_GLOBAL_SCALE, String.valueOf(mGlobalScale));
        edit.apply();
        super.onStop();
    }

    @Override
    public void onBackPressed() {
        stopAutoReload();
        if (mChatService != null) {
            mChatService.changeHandler(null);
        }
        super.onBackPressed();
    }

    void setConnectionStatus(int c){
        if (c == STATE_CONNECTED){
            m_btIconStatus.setColorFilter(Color.GREEN);
            m_btIconStatus.setImageResource(R.drawable.ic_link_ok);
        } else if (c == STATE_DISCONNECTED){
            m_btIconStatus.setColorFilter(Color.RED);
            m_btIconStatus.setImageResource(R.drawable.ic_link_nok);
        } else if (c == STATE_CONNECTING){
            m_btIconStatus.setColorFilter(Color.GRAY);
            m_btIconStatus.setImageResource(R.drawable.ic_link_ok);
        }
    }

    private void chooseCategory(){
        AlertDialog.Builder builder = new AlertDialog.Builder(this);
        builder.setTitle(getResources().getString(R.string.CATEGORY_CHOOSE));

        final String[] categories =
                m_currentLayoutData.getCategories().toArray(
                        new String[m_currentLayoutData.getCategories().size()]);

        builder.setItems(categories, (dialog, which) -> {
            String selected = categories[which];
            chooseScreen(selected);
        });

        AlertDialog dialog = builder.create();
        dialog.show();
    }

    private void chooseScreen(String screenname){
        AlertDialog.Builder builder = new AlertDialog.Builder(this);
        builder.setTitle(getResources().getString(R.string.SCREEN_CHOOSE));

        final String[] screens =
                m_currentLayoutData.getScreenNames(screenname).toArray(
                        new String[m_currentLayoutData.getScreenNames(screenname).size()]);

        builder.setItems(screens, (dialog, which) -> {
            String selected = screens[which];
            drawScreen(selected);
            m_currentScreenName = selected;
        });

        AlertDialog dialog = builder.create();
        dialog.show();
    }

    private void connectDevice() {
        if (isChatConnected() || isChatConnecting())
            return;

        mChatService.reconnect();
    }

    private boolean isChatConnected(){
        return mChatService != null && (mChatService.getState() == STATE_CONNECTED);
    }

    private boolean isChatConnecting(){
        return mChatService != null &&  (mChatService.getState() == STATE_CONNECTING);
    }

    private void initELM() {
        if (isChatConnected()) {
            mChatService.initElm();
            initBus();
        }
    }

    public void reconnect(){
        if(mChatService != null){
            mChatService.reconnect();
        }
    }

    private void initBus(){
        if (isChatConnected()) {
            if (m_ecu.getProtocol().equals("CAN")) {
                String txa = m_ecu.getTxId();
                String rxa = m_ecu.getRxId();
                mChatService.setEcuName(m_ecu.getName());
                mChatService.initCan(rxa, txa);
            } else if (m_ecu.getProtocol().equals("KWP2000")){
                String fa = m_ecu.getFunctionnalAddress();
                mChatService.initKwp(fa, m_ecu.getFastInit());
            } else if (m_ecu.getProtocol().equals("ISO8")){
                String fa = m_ecu.getFunctionnalAddress();
                mChatService.initIso8(fa);
            }
            updateDisplays();
        }
    }

    private void sendCmd(String cmd) {
        // Check that we're actually connected before trying anything
        if (!isChatConnected()) {
            m_logView.append(getResources().getString(R.string.FRAME_NOT_SENT) + " : " + cmd + "\n");
            return;
        }

        // Send command
        mChatService.write(cmd);
    }

    private void sendDelay(int delay) {
        if (!isChatConnected()) {
            m_logView.append(getResources().getString(R.string.NO_CHAT_SESSION) + "\n");
            return;
        }

        // Send command
        mChatService.write("DELAY:" + delay);
    }

    private void setElMWorking(boolean isQueueEmpty){
        if (m_currentScreenData == null)
            return;
        if (!isQueueEmpty) {
            m_btCommStatus.setColorFilter(Color.GREEN);
            for (View button : m_buttonsViews.values()){
                button.setEnabled(false);
            }
        } else {
            m_btCommStatus.clearColorFilter();
            for (View button : m_buttonsViews.values()){
                button.setEnabled(true);
            }
        }
        if (isQueueEmpty && m_autoReload){
            updateDisplays();
        }
    }

    void handleElmResult(String result){
        String[] results = result.split(";");
        if (results.length < 2 || results[0] == null || results[1] == null){
            m_logView.append(getResources().getString(R.string.NO_ELM_RESPONSE) + " (" + result + ")\n");
            return;
        }

        String requestCode = results[0];
        String replyCode = results[1];

        if (requestCode.length() >= 2 && requestCode.substring(0,2).equalsIgnoreCase("AT")){
            // Don't worry about ELM configuration
            return;
        }

        if (requestCode.length() >= 2 && requestCode.startsWith("14")){
            if (replyCode.length() >= 2 && replyCode.startsWith("54")){
                m_logView.append(getResources().getString(R.string.DTC_CLEAR_OK) + "\n");
                return;
            }
        }

        if (replyCode.length() >= 6 && replyCode.startsWith("7F")) {
            String resultCode = replyCode.substring(0, 6).toUpperCase();
            String nrcode = resultCode.substring(4, 6);
            String translatedErrorCode = mChatService.getEcuErrorCode(nrcode);
            if (translatedErrorCode != null){
                m_logView.append(getResources().getString(R.string.NEGATIVE_RESPONSE) +
                        " : " + translatedErrorCode + " (" + resultCode + ")\n");
                return;
            } else {
                m_logView.append(getResources().getString(R.string.NEGATIVE_RESPONSE) +
                        " : "  + resultCode + "\n");
                return;
            }
        } else {
            m_logView.append(getResources().getString(R.string.ELM_RESPONSE) +
                    " : " + replyCode + " " + getResources().getString(R.string.TO_REQUEST) +
                    " " + requestCode + "\n");
        }

        if (replyCode.length() >= 5 && replyCode.startsWith("ERROR")){
            m_logView.append(getResources().getString(R.string.BAD_RESPONSE) + " : "+ replyCode +
                    " " +getResources().getString(R.string.TO_REQUEST)+ " '" + requestCode + "'\n");
            return;
        }

        if (requestCode.equals(m_currentDtcRequestBytes)){
            decodeDTC(replyCode);
            m_currentDtcRequestBytes = "";
            return;
        }

        updateScreen(requestCode, replyCode);
    }

    void readDTC(){
        Ecu.EcuRequest dtcRequest = m_ecu.getRequest("ReadDTCInformation.ReportDTC");
        if (dtcRequest == null)
            dtcRequest = m_ecu.getRequest("ReadDTC");
        if (dtcRequest == null){
            Toast.makeText(getApplicationContext(), "No READ_DTC request in this file",
                    Toast.LENGTH_SHORT).show();
            return;
        }
        m_currentDtcRequestName = dtcRequest.name;
        m_currentDtcRequestBytes = dtcRequest.sentbytes;
        sendCmd(m_ecu.getDefaultSDS());
        sendCmd(m_currentDtcRequestBytes);
    }

    void clearDTC(){
        if (mDemoMode){
            return;
        }
        Ecu.EcuRequest clearDTCRequest = m_ecu.getRequest("ClearDiagnosticInformation.All");
        if (clearDTCRequest == null)
            clearDTCRequest = m_ecu.getRequest("ClearDTC");
        if (clearDTCRequest == null)
            clearDTCRequest = m_ecu.getRequest("Clear Diagnostic Information");

        if (clearDTCRequest != null){
            m_clearDTCCommand = clearDTCRequest.sentbytes;
        } else {
            m_clearDTCCommand = "14FF00";
        }

        DialogInterface.OnClickListener dialogClickListener = (dialog, which) -> {
            switch (which){
                case DialogInterface.BUTTON_POSITIVE:
                    sendCmd("AT ST FF");
                    sendCmd(m_ecu.getDefaultSDS());
                    sendCmd(m_clearDTCCommand);
                    sendCmd("AT ST 00");
                    break;

                case DialogInterface.BUTTON_NEGATIVE:
                    return;
            }
        };

        AlertDialog.Builder builder = new AlertDialog.Builder(this);
        builder.setMessage(getResources().getString(R.string.CLEAR_ALL_DTC))
                .setPositiveButton(getResources().getString(R.string.YES), dialogClickListener)
                .setNegativeButton(getResources().getString(R.string.NO), dialogClickListener).show();

    }

    void decodeDTC(String response){
        // Test data ACU4
        // response = "57 06 90 07 41 90 08 41 90 42 52 90 08 42 90 07 42 90 7C 40".replace(" ", "");
        List<List<String>> decodedDtcs = m_ecu.decodeDTC(m_currentDtcRequestName, response);

        if (decodedDtcs.size() == 0){
            Toast.makeText(getApplicationContext(), getResources().getString(R.string.NO_DTC_STORED),
                    Toast.LENGTH_SHORT).show();
            return;
        }

        StringBuilder dtcReport = new StringBuilder();
        int i = 0;
        for (List<String> stringList : decodedDtcs){
            dtcReport.append("<b>DTC #").append(i + 1).append("</b><br>");
            i++;
            for (String dtcLine : stringList){
                dtcReport.append("* ").append(dtcLine).append("<br>");
            }
        }

        Spanned message = Html.fromHtml(dtcReport.toString());
        AlertDialog alertDialog = new AlertDialog.Builder(ScreenActivity.this).create();
        alertDialog.setTitle("DTC Report");
        alertDialog.setMessage(message);
        alertDialog.setButton(AlertDialog.BUTTON_NEUTRAL, getResources().getString(R.string.OK),
                (dialog, which) -> dialog.dismiss());
        alertDialog.show();
    }

    private static class messageHandler extends Handler {
        private final ScreenActivity activity;
        messageHandler(ScreenActivity ac){
            activity = ac;
        }

        public void handleMessage(Message msg) {
            switch (msg.what) {
                case MESSAGE_STATE_CHANGE:
                    //if (BuildConfig.DEBUG)
                    //    Log.i(TAG, "MESSAGE_STATE_CHANGE: " + msg.arg1);
                    switch (msg.arg1) {
                        case STATE_CONNECTED:
                            activity.initELM();
                            activity.setConnectionStatus(STATE_CONNECTED);
                            break;
                        case STATE_CONNECTING:
                            activity.setConnectionStatus(STATE_CONNECTING);
                            break;
                        case STATE_NONE:
                        case STATE_DISCONNECTED:
                            activity.setConnectionStatus(STATE_DISCONNECTED);
                            activity.reconnect();
                            break;
                    }
                    break;
                case MESSAGE_READ:
                    try {
                        byte[] m = (byte[]) msg.obj;
                        String readMessage = new String(m, 0, msg.arg1);
                        activity.handleElmResult(readMessage);
                    } catch (Exception e) {
                        activity.m_logView.append("Java exception : " + e + "\n");
                    }
                    break;
                case MESSAGE_DEVICE_NAME:
                    activity.mConnectedDeviceName = msg.getData().getString(DEVICE_NAME);
                    activity.m_logView.append(activity.getResources().getString(R.string.NEW_DEVICE)
                            + " : " + activity.mConnectedDeviceName + "\n");
                    break;
                case MESSAGE_TOAST:
                    Toast.makeText(activity.getApplicationContext(), msg.getData().getString(TOAST),
                            Toast.LENGTH_SHORT).show();
                    break;
                case MESSAGE_LOG:
                    activity.m_logView.append(activity.getResources()
                            .getString(R.string.BT_MANAGER_MESSAGE) + " : " +
                            msg.getData().getString(TOAST) + "\n");
                    break;
                case MESSAGE_QUEUE_STATE:
                    int queue_len = msg.arg1;
                    activity.setElMWorking(queue_len == 0);
                    break;
            }
        }
    }
}
