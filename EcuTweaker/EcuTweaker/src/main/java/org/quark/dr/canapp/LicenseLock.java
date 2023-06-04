package org.quark.dr.canapp;

import org.quark.dr.ecu.Ecu;

public class LicenseLock {
    private int mAndroidID;
    private String mPublicCode;
    private String mPrivateCode;
    private boolean mLicenseOk;
    final static private String mAlphabet = "abcdefghijkmnpqrstuvwxyz23456789";
    final static private int mScrambleIndexes[] = new int[]{ 0, 20, 2, 17, 19, 5, 16, 14,
            8, 9, 10, 23, 12, 13, 7, 15,
            6, 3, 18, 4, 1, 21, 22, 11};

    public LicenseLock(long androidID){
        mLicenseOk = false;
        mAndroidID = getReducedID(androidID);
        String hexPadded = Ecu.padLeft(Integer.toHexString(mAndroidID), 6, "0");
        mPublicCode = addArmor(hexPadded.getBytes());
    }

    public String getPublicCode(){
        return mPublicCode;
    }

    public boolean isLicenseOk(){
        return mLicenseOk;
    }

    private int getScrambleIndex(int idx){
        for (int i = 0; i < 24; ++i){
            if (mScrambleIndexes[i] == idx)
                return i;
        }
        return -1;
    }

    private String xorOp(int l){
        long code = 45467;
        long xorOp = l ^ code;
        return new String(Ecu.padLeft(Long.toBinaryString(xorOp), 24, "0"));
    }

    private String scramble(String toScramble){
        String scrambled = "";
        for (int i = 0; i < 24; ++i){
            scrambled += toScramble.toCharArray()[mScrambleIndexes[i]];
        }
        return scrambled;
    }

    private String unscramble(String toUnscramble){
        String unscrambled = "";
        for (int i = 0; i < 24; ++i){
            unscrambled += toUnscramble.toCharArray()[getScrambleIndex(i)];
        }
        return unscrambled;
    }

    /*
     * Check unscrambled + xor'ed == mAndroidID
     */
    public boolean checkUnlock(String unlockCode){
        try {
            String removedArmor = new String(removeArmor(unlockCode));
            removedArmor = Ecu.padLeft(Integer.toBinaryString(Integer.parseInt(removedArmor, 16)), 24, "0");
            String unscrambledLockCode = unscramble(removedArmor);
            int integerLockCode = Integer.parseInt(unscrambledLockCode, 2);
            String xoredResult = xorOp(integerLockCode);
            int result = Integer.parseInt(xoredResult, 2);
            if (result == mAndroidID) {
                mLicenseOk = true;
                mPrivateCode = unlockCode;
                return true;
            }
        } catch (Exception e) {

        }
        mLicenseOk = false;
        return false;
    }

    public String getPrivateCode(){
        return mPrivateCode;
    }

    /*
     * Send mAndroidID xor'ed  + scrambled
     */
    public String generatePrivateCode(){
        String xored = xorOp(mAndroidID);
        String scrambledHex = Integer.toHexString(Integer.parseInt(scramble(xored), 2));
        String armored = new String(addArmor(scrambledHex.getBytes()));
        return armored;
    }

    private int getReducedID(long id){
        return (int)(id & 0xFFFFFF);
    }

    static public String addArmor(byte[] buf)
    {
        String result = "";
        int size = buf.length;
        for (int bit=0; bit < size*8; bit+=5) {
            int bit7 = bit & 7;
            int rest = 8 - bit7;
            int fivebits = ((buf[bit/8] >> bit7) & 0x1f);
            if ((bit/8+1) < size)
                fivebits |= ((buf[bit/8+1] & (0x1f >> rest)) << rest);
            result += mAlphabet.toCharArray()[fivebits];
        }
        return result;
    }

    static public byte[] removeArmor(String armoredString)
    {
        char[] armoredCharArray = armoredString.toCharArray();
        int textlen = armoredString.length();
        int result_size = (textlen*5) / 8;
        byte result[] = new byte[result_size];

        for (int idx=0; idx < textlen; ++idx) {
            int fivebits = mAlphabet.indexOf(armoredCharArray[idx]);
            if (fivebits < 0) return result;
            int bb = (idx * 5) / 8;
            int bit  = (idx * 5) & 0x07;
            int rest = 8 - bit;
            result[bb]   |= (fivebits << bit) & 0xFF;
            if (bb+1 < result_size)
                result[bb+1] |= (fivebits >> rest) & 0xFF;
        }
        return result;
    }
}
