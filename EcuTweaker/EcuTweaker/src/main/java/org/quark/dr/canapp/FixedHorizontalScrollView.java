package org.quark.dr.canapp;

import android.content.Context;
import android.util.AttributeSet;
import android.widget.HorizontalScrollView;

public class FixedHorizontalScrollView extends HorizontalScrollView {
    public FixedHorizontalScrollView(Context context, AttributeSet attrs, int defStyle) {
        super(context, attrs, defStyle);
    }

    public FixedHorizontalScrollView(Context context, AttributeSet attrs) {
        super(context, attrs);
    }

    public FixedHorizontalScrollView(Context context) {
        super(context);
    }


    @Override
    protected int computeScrollDeltaToGetChildRectOnScreen(android.graphics.Rect rect) {
        return 0;
    }
}
