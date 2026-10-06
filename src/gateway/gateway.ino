// Pico LoRa RX -> SIM800L SMS gateway (Arduino / Earle Philhower RP2040 core).
// Boards: Raspberry Pi Pico. Libraries: Sandeep Mistry LoRa (sandeepmistry).
// Wiring Pico: NSS 5, RST 6, DIO0 7, SPI0 SCK 2 MOSI 3 MISO 4 (Ra-02 3V3, antenna on).
// SIM800L: UART1 TX GP8 -> divider -> SIM RX, RX GP9 <- SIM TX, 4.0V 2A buck + cap, common GND.
// Config: set LORA_FREQ, RECIPIENTS below. USB Serial = log for PC monitoring.

#include <SPI.h>
#include <LoRa.h>

#define LORA_NSS 5
#define LORA_RST 6
#define LORA_DIO0 7
#define LORA_FREQ 433E6
#define LORA_SF 9

#define SIM_UART_TX 8  // Pico TX -> SIM RX
#define SIM_UART_RX 9  // Pico RX <- SIM TX

const char* RECIPIENTS[] = {"+91XXXXXXXXXX"};  // <-- set ranger numbers
const int N_RECIPIENTS = 1;

#define MAX_SEEN 32
String seenKeys[MAX_SEEN];
unsigned long seenTs[MAX_SEEN];
int seenN = 0;

bool isDup(String key) {
  unsigned long now = millis();
  for (int i = 0; i < seenN; i++) {
    if (now - seenTs[i] > 60000UL) {  // expire, compact
      for (int j = i; j < seenN - 1; j++) { seenKeys[j] = seenKeys[j+1]; seenTs[j] = seenTs[j+1]; }
      seenN--; i--;
    }
  }
  for (int i = 0; i < seenN; i++) if (seenKeys[i] == key) return true;
  if (seenN < MAX_SEEN) { seenKeys[seenN] = key; seenTs[seenN] = now; seenN++; }
  return false;
}

bool atCmd(const char* cmd, const char* expect, unsigned long waitMs) {
  Serial1.print(cmd); Serial1.print("\r\n");
  unsigned long t0 = millis(); String buf = "";
  while (millis() - t0 < waitMs) {
    while (Serial1.available()) { buf += (char)Serial1.read(); }
    if (buf.indexOf(expect) >= 0) return true;
    if (buf.indexOf("ERROR") >= 0) return false;
  }
  return buf.indexOf(expect) >= 0;
}

bool sendSms(const char* num, String text) {
  if (!atCmd("AT", "OK", 5000)) return false;
  atCmd("ATE0", "OK", 2000);
  if (!atCmd("AT+CMGF=1", "OK", 3000)) return false;
  String cmgs = String("AT+CMGS=\"") + num + "\"";
  Serial1.print(cmgs + "\r\n");
  delay(1000);
  Serial1.print(text + (char)26);
  unsigned long t0 = millis(); String buf = "";
  while (millis() - t0 < 15000) {
    while (Serial1.available()) buf += (char)Serial1.read();
    if (buf.indexOf("OK") >= 0) return true;
    if (buf.indexOf("ERROR") >= 0) return false;
  }
  return false;
}

// Minimal validate: F01|S|P1V1S1|92|1935|78|042 -> sms text. Returns "" if bad.
String toSms(String raw, String &dedupeKey, bool &isSuspicious) {
  raw.trim();
  if (raw.length() == 0 || raw.length() > 64) return "";
  int p[8]; int n = 0; p[0] = -1;
  for (int i = 0; i < (int)raw.length() && n < 7; i++) if (raw[i] == '|') p[++n] = i;
  if (n != 6) return "";
  String node = raw.substring(0, p[1]);
  String ev = raw.substring(p[1]+1, p[2]);
  String fl = raw.substring(p[2]+1, p[3]);
  String cf = raw.substring(p[3]+1, p[4]);
  String hm = raw.substring(p[4]+1, p[5]);
  String bt = raw.substring(p[5]+1, p[6]);
  String sq = raw.substring(p[6]+1);
  if (node.length() != 3 || (ev != "S" && ev != "N") || fl.length() != 6) return "";
  int conf = cf.toInt(), batt = bt.toInt(), seq = sq.toInt();
  if (hm.length() != 4) return "";
  if (conf < 0 || conf > 100 || batt < 0 || batt > 100 || seq < 0 || seq > 255) return "";
  dedupeKey = node + ":" + String(seq);
  isSuspicious = (ev == "S");
  return "ALERT " + node + " " + (isSuspicious ? "SUS " : "OK ") + fl + " " + String(conf) + "% " + hm + " B" + String(batt) + "%";
}

void setup() {
  Serial.begin(115200);
  Serial1.setTX(SIM_UART_TX); Serial1.setRX(SIM_UART_RX);
  Serial1.begin(9600);
  LoRa.setPins(LORA_NSS, LORA_RST, LORA_DIO0);
  LoRa.setSPIFrequency(5E6);
  if (!LoRa.begin(LORA_FREQ)) { Serial.println("LoRa init failed"); while (1) delay(1000); }
  LoRa.setSpreadingFactor(LORA_SF);
  LoRa.setSignalBandwidth(125E3);
  LoRa.setSyncWord(0x12);
  Serial.println("GW ready: LoRa RX -> SMS");
}

void loop() {
  int sz = LoRa.parsePacket();
  if (sz) {
    String raw = "";
    while (LoRa.available()) raw += (char)LoRa.read();
    Serial.println("RX: " + raw);
    String key; bool susp = false;
    String sms = toSms(raw, key, susp);
    if (sms == "") { Serial.println("bad packet"); return; }
    if (isDup(key)) { Serial.println("dupe ignored"); return; }
    Serial.println("LOG: " + sms);
    if (susp) {
      for (int i = 0; i < N_RECIPIENTS; i++) {
        bool ok = sendSms(RECIPIENTS[i], sms);
        Serial.println(String("SMS ") + RECIPIENTS[i] + (ok ? " OK" : " FAIL"));
        delay(2000);
      }
    }
  }
}
