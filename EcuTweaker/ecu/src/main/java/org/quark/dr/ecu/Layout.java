package org.quark.dr.ecu;

import android.util.Pair;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Set;

public class Layout {
    public HashMap<String, ScreenData> m_screens;
    HashMap<String, ArrayList<String>> m_categories;

    private static class ListComparator implements Comparator {

        @Override
        public int compare(Object o1, Object o2) {
            Pair<Integer, String> O1 = (Pair<Integer, String>)o1;
            Pair<Integer, String> O2 = (Pair<Integer, String>)o2;
            return O2.first - O1.first;
        }
    }

    public static class Color {
        int r,g,b;

        Color(){
            r = g = b = 0;
        }

        Color(JSONObject jobj, String tag){
            try {
                r = g = b = 10;
                if (jobj.has(tag)){
                    String scol = jobj.getString(tag);
                    scol = scol.substring(4, scol.length() -1);
                    String[] cols = scol.split(",");
                    if (cols.length == 3) {
                        r = Integer.parseInt(cols[0]);
                        g = Integer.parseInt(cols[1]);
                        b = Integer.parseInt(cols[2]);
                    }
                }
            } catch (Exception e) {
                e.printStackTrace();
            }
        }

        public int get(){
            return 255 << 24 | r << 16 | g << 8 | b;
        }
    }

    public static class Font {
        public String name;
        public int size;
        public Color color;
        public Font(JSONObject fobj){
            color = new Color();
            size = 10;
            try {
                if (fobj.has("name")) name = fobj.getString("name");
                if (fobj.has("size")) size = fobj.getInt("size");
                if (fobj.has("color")) color = new Color(fobj, "color");
            } catch (Exception e) {
                e.printStackTrace();
            }
        }
    }

    public static class Rect {
        public int x, y, w, h, area;
        Rect(JSONObject jrect){
            try {
                if (jrect.has("width")) w = jrect.getInt("width");
                if (jrect.has("height")) h = jrect.getInt("height");
                if (jrect.has("top")) y = jrect.getInt("top");
                if (jrect.has("left")) x = jrect.getInt("left");
                area = w * h;
            } catch (Exception e) {
                e.printStackTrace();
            }
        }
    }

    public static class InputData {
        public String text;
        public String request;
        public Rect rect;
        public int width;
        public Font font;
        public Color color;
    }

    public static class DisplayData {
        public String text;
        public String request;
        public Rect rect;
        public int width;
        public Font font;
        public Color color;
    }

    public static class LabelData {
        public String text;
        public Rect rect;
        public Font font;
        public int alignment;
        public Color color, fontcolor;
    }

    public static class ButtonData {
        public String text, uniqueName;
        public Rect rect;
        public Font font;
        public ArrayList<Pair<Integer, String>> sendData;
    }


    public static class ScreenData {
        List<InputData> m_inputs;
        List<LabelData> m_labels;
        List<DisplayData> m_displays;
        List<ButtonData> m_buttons;
        public String m_screen_name;
        public int m_width, m_height;
        public Color m_color;
        public ArrayList<Pair<Integer, String>> preSendData;

        ScreenData(String name, JSONObject jobj){
            m_inputs = new ArrayList<>();
            m_labels = new ArrayList<>();
            m_displays = new ArrayList<>();
            m_buttons = new ArrayList<>();

            m_screen_name = name;

            try {
                if (jobj.has("presend")) {
                    JSONArray sendData = jobj.getJSONArray("presend");
                    preSendData = new ArrayList<>();
                    for (int j = 0; j < sendData.length(); ++j) {
                        JSONObject jdata = sendData.getJSONObject(j);
                        Pair<Integer, String> pair = new Pair<>(Integer.parseInt(jdata.getString("Delay")), jdata.getString("RequestName"));
                        preSendData.add(pair);
                    }
                }
            } catch (Exception e) {
                e.printStackTrace();
            }

            try {
                if (jobj.has("width")) m_width = jobj.getInt("width");
                if (jobj.has("height")) m_height = jobj.getInt("height");
                if (jobj.has("color")) m_color = new Color(jobj, "color");

                JSONArray jinputs = jobj.getJSONArray("inputs");
                for (int i = 0; i < jinputs.length(); ++i) {
                    JSONObject inputobj = jinputs.getJSONObject(i);
                    InputData data = new InputData();
                    if (inputobj.has("text")) data.text = inputobj.getString("text");
                    if (inputobj.has("request")) data.request = inputobj.getString("request");
                    if (inputobj.has("width")) data.width = inputobj.getInt("width");
                    if (inputobj.has("rect")) data.rect = new Rect(inputobj.getJSONObject("rect"));
                    if (inputobj.has("font")) data.font = new Font(inputobj.getJSONObject("font"));
                    if (inputobj.has("color")) data.color = new Color(inputobj, "color");
                    m_inputs.add(data);
                }
            } catch (Exception e) {
                e.printStackTrace();
            }

            try {
                JSONArray jinputs = jobj.getJSONArray("displays");
                for (int i = 0; i < jinputs.length(); ++i) {
                    JSONObject displayobj = jinputs.getJSONObject(i);
                    DisplayData data = new DisplayData();
                    if (displayobj.has("text")) data.text = displayobj.getString("text");
                    if (displayobj.has("request")) data.request = displayobj.getString("request");
                    if (displayobj.has("width")) data.width = displayobj.getInt("width");
                    if (displayobj.has("rect")) data.rect = new Rect(displayobj.getJSONObject("rect"));
                    if (displayobj.has("font")) data.font = new Font(displayobj.getJSONObject("font"));
                    if (displayobj.has("color")) data.color = new Color(displayobj, "color");
                    m_displays.add(data);
                }
            } catch (Exception e) {
                e.printStackTrace();
            }

            try {
                JSONArray linputs = jobj.getJSONArray("labels");
                List<Pair<Integer, LabelData>> areaSort = new ArrayList<>();
                for (int i = 0; i < linputs.length(); ++i) {
                    JSONObject inputobj = linputs.getJSONObject(i);
                    LabelData data = new LabelData();
                    if (inputobj.has("text")) data.text = inputobj.getString("text");
                    if (inputobj.has("bbox")) data.rect = new Rect(inputobj.getJSONObject("bbox"));
                    if (inputobj.has("font")) data.font = new Font(inputobj.getJSONObject("font"));
                    if (inputobj.has("fontcolor")) data.fontcolor = new Color(inputobj, "fontcolor");
                    if (inputobj.has("alignment")) data.alignment = inputobj.getInt("alignment");
                    if (inputobj.has("color")) data.color = new Color(inputobj, "color");
                    areaSort.add(new Pair<>(data.rect.area, data));
                }

                Collections.sort(areaSort, new ListComparator());
                for (Pair<Integer, LabelData> pair: areaSort){
                    m_labels.add(pair.second);
                }

            } catch (Exception e) {
                e.printStackTrace();
            }

            try {
                JSONArray binputs = jobj.getJSONArray("buttons");
                for (int i = 0; i < binputs.length(); ++i) {
                    JSONObject inputobj = binputs.getJSONObject(i);
                    ButtonData data = new ButtonData();
                    if (inputobj.has("text")) data.text = inputobj.getString("text");
                    if (inputobj.has("rect")) data.rect = new Rect(inputobj.getJSONObject("rect"));
                    if (inputobj.has("font")) data.font = new Font(inputobj.getJSONObject("font"));
                    if (inputobj.has("uniquename")) data.uniqueName = inputobj.getString("uniquename");
                    if (inputobj.has("send")) {
                        JSONArray sendData = inputobj.getJSONArray("send");
                        data.sendData = new ArrayList<>();
                        for (int j = 0; j < sendData.length(); ++j) {
                            JSONObject jdata = sendData.getJSONObject(j);
                            Pair<Integer, String> pair = new Pair<>(Integer.parseInt(jdata.getString("Delay")), jdata.getString("RequestName"));
                            data.sendData.add(pair);
                        }
                    }
                    m_buttons.add(data);
                }
            } catch (Exception e) {
                e.printStackTrace();
            }
        }

        public List<InputData> getInputs(){
            return m_inputs;
        }

        public List<LabelData> getLabels(){
            return m_labels;
        }

        public List<DisplayData> getDisplays(){
            return m_displays;
        }

        public List<ButtonData> getButtons(){
            return m_buttons;
        }

        public ButtonData getButtonData(String buttonname){
            for (ButtonData currentData : m_buttons) {
                if (currentData.uniqueName.equals(buttonname)) {
                    return currentData;
                }
            }
            return null;
        }

        public ArrayList<Pair<Integer, String>> getPreSendData(){
            return preSendData;
        }
    }

    public Layout(InputStream is){
        String line;
        BufferedReader br;
        StringBuilder sb = new StringBuilder();

        try {
            br = new BufferedReader(new InputStreamReader(is));
            while ((line = br.readLine()) != null) {
                sb.append(line).append("\n");
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

    public Layout(String js){
        try {
            init(new JSONObject(js));
        } catch (Exception e){
            e.printStackTrace();
        }
    }

    void init(JSONObject jobj){
        m_screens = new HashMap<>();
        m_categories = new HashMap<>();
        try {
            // Gather all screens
            if (jobj.has("screens")) {
                JSONObject scr_object = jobj.getJSONObject("screens");
                Iterator<String> keys = scr_object.keys();
                while (keys.hasNext()) {
                    String key = keys.next();
                    JSONObject sobj = scr_object.getJSONObject(key);
                    ScreenData sdata = new ScreenData(key, sobj);
                    m_screens.put(key, sdata);
                }
            }
        }  catch (Exception e) {
            e.printStackTrace();
        }

        try{

            JSONObject categories = jobj.getJSONObject("categories");
            Iterator<String> iterator = categories.keys();
            while(iterator.hasNext()) {
                String currentKey = iterator.next();
                ArrayList<String> screennames = new ArrayList<>();
                JSONArray jscreenarry = categories.getJSONArray(currentKey);
                for (int i = 0; i < jscreenarry.length(); ++i) {
                    screennames.add(jscreenarry.getString(i));
                }
                m_categories.put(currentKey, screennames);
            }

        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    public Set<String> getCategories(){
        return m_categories.keySet();
    }

    public ArrayList<String> getScreenNames(String category){
        return m_categories.get(category);
    }

    public ScreenData getScreen(String screenName){
        if(m_screens.containsKey(screenName)) {
            return m_screens.get(screenName);
        } else {
            return null;
        }
    }
}
