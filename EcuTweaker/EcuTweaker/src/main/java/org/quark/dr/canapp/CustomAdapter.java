package org.quark.dr.canapp;

import android.content.Context;
import androidx.annotation.NonNull;
import android.util.TypedValue;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ArrayAdapter;
import android.widget.TextView;

public class CustomAdapter extends ArrayAdapter<String> {
    Context context;
    int color;
    String[] items;
    private int textSize=20;

    public CustomAdapter(final Context context, final int textViewResourceId, final String[] objects) {
        super(context, textViewResourceId, objects);
        this.items = objects;
        this.context = context;

    }

    @Override
    public View getDropDownView(int position, View convertView,
                                @NonNull ViewGroup parent) {

        if (convertView == null) {
            LayoutInflater inflater = LayoutInflater.from(context);
            convertView = inflater.inflate(
                    android.R.layout.simple_spinner_item, parent, false);
        }

        TextView tv = convertView.findViewById(android.R.id.text1);
        tv.setText(items[position]);
        //tv.setTextSize(textSize);
        return convertView;
    }

    @Override
    public View getView(int position, View convertView, @NonNull ViewGroup parent) {
        if (convertView == null) {
            LayoutInflater inflater = LayoutInflater.from(context);
            convertView = inflater.inflate(
                    android.R.layout.simple_spinner_item, parent, false);
        }

        TextView tv = convertView.findViewById(android.R.id.text1);
        tv.setText(items[position]);
        tv.setTextColor(color);
        tv.setTextSize(TypedValue.COMPLEX_UNIT_PX, textSize);
        return convertView;
    }

    public void setSpinnerTextSize(int size){
        textSize= size;
    }
    public void setSpinnerTextColor(int color){
        this.color = color;
    }

}
