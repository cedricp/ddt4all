package org.quark.dr.canapp;

import android.content.Context;
import android.util.AttributeSet;
import android.widget.ScrollView;

public class FixedScrollView extends ScrollView {
    public FixedScrollView(Context context, AttributeSet attrs, int defStyle) {
        super(context, attrs, defStyle);
    }

    public FixedScrollView(Context context, AttributeSet attrs) {
        super(context, attrs);
    }

    public FixedScrollView(Context context) {
        super(context);
    }


    @Override
    protected int computeScrollDeltaToGetChildRectOnScreen(android.graphics.Rect rect) {
        return 0;
    }
}
