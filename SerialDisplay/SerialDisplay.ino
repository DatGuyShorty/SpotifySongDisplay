#include <Wire.h>
#include <LiquidCrystal_I2C.h>

LiquidCrystal_I2C lcd(0x27, 16, 2);

const unsigned long SCROLL_INTERVAL = 500;  // ms between scroll steps
const int SCROLL_GAP = 4;                   // spaces between repeats

String songName = "";
String artistName = "";

// scroll buffers
String scrollSong;
String scrollArtist;

bool scrollingNeeded = false;
int scrollPos = 0;
unsigned long lastScrollTime = 0;

// keep only LCD-safe chars
String filterPrintable(const String &in) {
  String out;
  for (char c : in) {
    out += (c >= 32 && c <= 126) ? c : ' ';
  }
  return out;
}

// return width-long window from src at pos
String scrollWindow(const String &src, int pos, int width) {
  String win;
  int len = src.length();
  for (int i = 0; i < width; i++) {
    win += src[(pos + i) % len];
  }
  return win;
}

// center a line that fits
String centerLine(const String &in) {
  int len = in.length();
  int left = (16 - len) / 2;
  String out;
  for (int i = 0; i < left; i++) out += ' ';
  out += in;
  while (out.length() < 16) out += ' ';
  return out;
}

void prepareScroll() {
  // clean up
  songName.replace("\\n", " ");
  artistName.replace("\\n", " ");
  songName.trim();
  artistName.trim();
  songName   = filterPrintable(songName);
  artistName = filterPrintable(artistName);

  scrollingNeeded = (songName.length() > 16) || (artistName.length() > 16);

  if (!scrollingNeeded) {
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print(centerLine(songName));
    lcd.setCursor(0, 1);
    lcd.print(centerLine(artistName));
  } else {
    // build base = text + gap
    String baseSong = songName;
    String baseArtist = artistName;
    for (int i = 0; i < SCROLL_GAP; i++) {
      baseSong   += ' ';
      baseArtist += ' ';
    }
    // double it for continuous wrap
    scrollSong   = baseSong + baseSong;
    scrollArtist = baseArtist + baseArtist;

    scrollPos      = 0;
    lastScrollTime = millis();

    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print(scrollWindow(scrollSong, 0, 16));
    lcd.setCursor(0, 1);
    lcd.print(scrollWindow(scrollArtist, 0, 16));
  }
}

void newMessage(const String &raw) {
  String clean = raw;
  clean.trim();
  int nl = clean.indexOf('\n');
  if (nl < 0) return;
  songName   = clean.substring(0, nl);
  artistName = clean.substring(nl + 1);
  prepareScroll();
}

void setup() {
  lcd.init();
  lcd.backlight();
  Serial.begin(9600);
}

void loop() {
  static String buf;
  while (Serial.available()) {
    buf += char(Serial.read());
    if (buf.endsWith("\n\n")) {
      newMessage(buf);
      buf = "";
      break;
    }
  }

  if (scrollingNeeded) {
    unsigned long now = millis();
    if (now - lastScrollTime >= SCROLL_INTERVAL) {
      lastScrollTime = now;
      lcd.setCursor(0, 0);
      lcd.print(scrollWindow(scrollSong, scrollPos, 16));
      lcd.setCursor(0, 1);
      lcd.print(scrollWindow(scrollArtist, scrollPos, 16));
      scrollPos++;
    }
  }
}
