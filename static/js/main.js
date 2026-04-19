class SignLanguageApp {
  constructor() {
    this.currentGesture = "--";
    this.lastGesture = "";
    this.gestureStability = 0;
    this.gestureHistory = [];
    this.stabilityThreshold = 3;
    this.confidenceScore = 0;
    this.cameraActive = true;
    this.videoFeed = null;
    this.settingsModal = null;
    this.aboutModal = null;
    this.signsModal = null;

    this.currentLocation = "unknown";
    this.currentMovement = "stationary";
    this.currentOrientation = "unknown";

    this.settings = {
      handshape: true,
      location: false,
      movement: false,
      palmOrientation: false,
      nonManual: false,
      grammar: false,
      iconicity: false,
      regional: false,
      showIndicators: false,
      confidenceDisplay: true,
    };

    this.init();
  }

  async init() {
    this.videoFeed = document.getElementById("videoFeed");
    this.settingsModal = new bootstrap.Modal(
      document.getElementById("settingsModal"),
    );
    this.aboutModal = new bootstrap.Modal(
      document.getElementById("aboutModal"),
    );
    this.signsModal = new bootstrap.Modal(
      document.getElementById("signsModal"),
    );

    this.setupEventListeners();
    this.loadSettings();
    this.startGestureMonitoring();
    this.startFeaturesMonitoring();
    this.startTextMonitoring();
    this.startTimeDisplay();
    this.animateConfidenceBar();
  }

  setupEventListeners() {
    document
      .getElementById("addGestureBtn")
      .addEventListener("click", () => this.addCurrentGesture());
    document
      .getElementById("addSpaceBtn")
      .addEventListener("click", () => this.addSpace());
    document
      .getElementById("backspaceBtn")
      .addEventListener("click", () => this.backspace());
    document
      .getElementById("clearTextBtn")
      .addEventListener("click", () => this.clearText());
    document
      .getElementById("clearTextHeaderBtn")
      .addEventListener("click", () => this.clearText());
    document
      .getElementById("settingsBtn")
      .addEventListener("click", () => this.settingsModal.show());
    document
      .getElementById("signsBtn")
      .addEventListener("click", () => this.signsModal.show());
    document.getElementById("aboutInfoBtn").addEventListener("click", () => {
      this.settingsModal.hide();
      this.aboutModal.show();
    });
    document
      .getElementById("resetSettingsBtn")
      .addEventListener("click", () => this.resetSettings());

    const cameraSwitch = document.getElementById("cameraSwitch");
    
    cameraSwitch.addEventListener("change", (e) =>
      this.toggleCamera(e.target.checked),
    );

    document.addEventListener("keydown", (e) => this.handleKeyboard(e));

    document.querySelectorAll("button").forEach((btn) => {
      btn.addEventListener("mousedown", (e) => e.preventDefault());
    });

    this.setupSettingsListeners();
  }

  setupSettingsListeners() {
    const settingsMap = {
      locationToggle: "location",
      movementToggle: "movement",
      palmOrientationToggle: "palmOrientation",
      nonManualToggle: "nonManual",
      grammarToggle: "grammar",
      iconicityToggle: "iconicity",
      regionalToggle: "regional",
      showIndicatorsToggle: "showIndicators",
      confidenceDisplayToggle: "confidenceDisplay",
    };

    Object.entries(settingsMap).forEach(([elementId, settingKey]) => {
      const element = document.getElementById(elementId);
      if (element) {
        element.checked = this.settings[settingKey];

        element.addEventListener("change", (e) => {
          this.settings[settingKey] = e.target.checked;
          this.saveSettings();
          this.updateFeatureIndicators();
          this.showFeedback(
            `${this.getSettingName(settingKey)} ${e.target.checked ? "enabled" : "disabled"}`,
            "info",
          );
        });
      }
    });
  }

  getSettingName(key) {
    const names = {
      location: "Location",
      movement: "Movement",
      palmOrientation: "Palm Orientation",
      nonManual: "Non-Manual Features",
      grammar: "Grammatical Structure",
      iconicity: "Iconicity",
      regional: "Regional Variants",
      showIndicators: "Feature Indicators",
      confidenceDisplay: "Confidence Display",
    };
    return names[key] || key;
  }

  saveSettings() {
    localStorage.setItem("signLanguageSettings", JSON.stringify(this.settings));
  }

  loadSettings() {
    const saved = localStorage.getItem("signLanguageSettings");
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        Object.assign(this.settings, parsed);
      } catch (e) {}
    }
  }

  resetSettings() {
    this.settings = {
      handshape: true,
      location: false,
      movement: false,
      palmOrientation: false,
      nonManual: false,
      grammar: false,
      iconicity: false,
      regional: false,
      showIndicators: false,
      confidenceDisplay: true,
    };

    Object.entries({
      locationToggle: "location",
      movementToggle: "movement",
      palmOrientationToggle: "palmOrientation",
      nonManualToggle: "nonManual",
      grammarToggle: "grammar",
      iconicityToggle: "iconicity",
      regionalToggle: "regional",
      showIndicatorsToggle: "showIndicators",
      confidenceDisplayToggle: "confidenceDisplay",
    }).forEach(([id, key]) => {
      const el = document.getElementById(id);
      if (el) el.checked = this.settings[key];
    });

    this.saveSettings();
    this.updateFeatureIndicators();
    this.showFeedback("Settings reset to default", "info");
  }

  updateFeatureIndicators() {
    const container = document.getElementById("featureIndicators");
    if (!container) return;

    if (!this.settings.showIndicators || !this.cameraActive) {
      container.innerHTML = "";
      return;
    }

    const activeFeatures = [];

    if (this.settings.location)
      activeFeatures.push(`LOC:${this.currentLocation}`);

    if (this.settings.movement)
      activeFeatures.push(`MOV:${this.currentMovement}`);

    if (this.settings.palmOrientation)
      activeFeatures.push(`ORI:${this.currentOrientation}`);

    if (this.settings.nonManual) activeFeatures.push("NMF");

    if (this.settings.grammar) activeFeatures.push("GRM");

    if (this.settings.iconicity) activeFeatures.push("ICO");

    if (this.settings.regional) activeFeatures.push("REG");

    container.innerHTML = activeFeatures
      .map((f) => `<span class="feature-badge">${f}</span>`)
      .join("");
  }

  toggleCamera(isActive) {
    this.cameraActive = isActive;
    const videoFeed = document.getElementById("videoFeed");
    const cameraOfflay = document.getElementById("cameraOfflay");
    const statusDot = document.getElementById("statusDot");
    const statusText = document.getElementById("statusText");
    const systemStatusText = document.getElementById("systemStatusText");
    const liveGesture = document.getElementById("liveGesture");

    if (isActive) {
      videoFeed.classList.remove("hidden");
      cameraOfflay.classList.remove("visible");
      videoFeed.src = "video_feed";
      statusDot.classList.remove("offline");
      statusText.textContent = "Live";
      systemStatusText.textContent = "Active";
      liveGesture.textContent = "Initializing...";
      this.updateFeatureIndicators();
      this.showFeedback("Camera activated", "success");
    } else {
      videoFeed.classList.add("hidden");
      cameraOfflay.classList.add("visible");
      videoFeed.src = "";
      statusDot.classList.add("offline");
      statusText.textContent = "Offline";
      systemStatusText.textContent = "Standby";
      liveGesture.textContent = "Camera Off";
      document.getElementById("featureIndicators").innerHTML = "";
      this.updateGestureDisplay("--", 0);
      this.showFeedback("Camera deactivated", "info");
    }
  }

  handleKeyboard(event) {
    if (event.target.tagName === "INPUT" || event.target.tagName === "TEXTAREA")
      return;

    switch (event.key) {
      case " ":
        event.preventDefault();
        this.addSpace();
        break;
      case "Backspace":
        event.preventDefault();
        this.backspace();
        break;
      case "Enter":
        event.preventDefault();
        this.addCurrentGesture();
        break;
      case "Escape":
        event.preventDefault();
        this.clearText();
        break;
      case "c":
      case "C":
        if (event.ctrlKey) {
          event.preventDefault();
          this.clearText();
        }
        break;
    }
  }

  async startGestureMonitoring() {
    const updateGesture = async () => {
      if (!this.cameraActive) {
        setTimeout(updateGesture, 200);
        return;
      }
      try {
        const response = await fetch("/get_gesture");
        const data = await response.json();
        if (data.gesture) this.processGesture(data.gesture);
      } catch (error) {
        this.updateGestureDisplay("Error", 0);
      }
      setTimeout(updateGesture, 200);
    };
    updateGesture();
  }

  async startFeaturesMonitoring() {
    const updateFeatures = async () => {
      if (!this.cameraActive) {
        setTimeout(updateFeatures, 500);
        return;
      }

      try {
        const response = await fetch("/get_all_features");
        const data = await response.json();
        this.currentLocation = data.location || "unknown";
        this.currentMovement = data.movement || "stationary";
        this.currentOrientation = data.orientation || "unknown";
        this.confidenceScore = data.confidence || 0;
        this.updateFeatureIndicators();
      } catch (error) {}

      setTimeout(updateFeatures, 500);
    };
    updateFeatures();
  }

  processGesture(gesture) {
    this.gestureHistory.push(gesture);
    if (this.gestureHistory.length > 10) this.gestureHistory.shift();

    if (gesture === this.lastGesture) {
      this.gestureStability++;
    } else {
      this.gestureStability = 0;
      this.lastGesture = gesture;
    }

    this.confidenceScore = Math.min(
      (this.gestureStability / this.stabilityThreshold) * 100,
      100,
    );

    if (
      this.gestureStability >= this.stabilityThreshold ||
      gesture !== this.currentGesture
    ) {
      this.updateGestureDisplay(gesture, this.confidenceScore);
      if (
        this.gestureStability === this.stabilityThreshold &&
        gesture !== "No hand detected" &&
        gesture !== "Unknown" &&
        gesture !== "Error" &&
        gesture !== "--"
      ) {
        this.autoAddGesture(gesture);
      }
    }

    const liveGestureEl = document.getElementById("liveGesture");
    if (liveGestureEl) liveGestureEl.textContent = gesture;
  }

  updateGestureDisplay(gesture, confidence) {
    const gestureElement = document.getElementById("currentGesture");
    const confidenceBar = document.getElementById("confidenceBar");
    const gestureIcon = document.getElementById("gestureIcon");

    if (gestureElement && gestureElement.textContent !== gesture) {
      gestureElement.textContent = gesture;
      gestureElement.classList.add("gesture-pop");
      setTimeout(() => gestureElement.classList.remove("gesture-pop"), 300);
    }

    if (confidenceBar) {
      if (this.settings.confidenceDisplay) {
        confidenceBar.style.width = confidence + "%";
        if (confidence > 70)
          confidenceBar.style.background =
            "linear-gradient(135deg, #5cb896 0%, #4aa87e 100%)";
        else if (confidence > 40)
          confidenceBar.style.background =
            "linear-gradient(135deg, #e8a874 0%, #d89060 100%)";
        else
          confidenceBar.style.background =
            "linear-gradient(135deg, #e8747a 0%, #d46066 100%)";
      } else {
        confidenceBar.style.width = "0%";
      }
    }

    if (gestureIcon) this.updateGestureIcon(gestureIcon, gesture);
    this.currentGesture = gesture;
  }

  updateGestureIcon(iconElement, gesture) {
    const iconMap = {
      A: "hand-fist",
      B: "hand",
      C: "hand-wave",
      D: "hand-pointing",
      E: "hand-fist",
      F: "hand-ok",
    };
    const iconName = iconMap[gesture] || "hand";
    iconElement.innerHTML = `<i class="fi fi-rr-${iconName}"></i>`;
  }

  async autoAddGesture(gesture) {
    if (this.confidenceScore > 80 && this.cameraActive)
      await this.addGesture(gesture);
  }

  async addCurrentGesture() {
    if (!this.cameraActive) {
      this.showFeedback("Camera is off", "error");
      return;
    }
    if (
      this.currentGesture &&
      this.currentGesture !== "No hand detected" &&
      this.currentGesture !== "Unknown" &&
      this.currentGesture !== "Error" &&
      this.currentGesture !== "--"
    ) {
      await this.addGesture(this.currentGesture);
    }
  }

  async addGesture(gesture) {
    try {
      const response = await fetch("/add_to_text", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ gesture: gesture }),
      });
      if (response.ok) {
        this.showFeedback(`Added: ${gesture}`, "success");
        await this.updateOutputText();
      }
    } catch (error) {
      this.showFeedback("Failed", "error");
    }
  }

  async startTextMonitoring() {
    const updateText = async () => {
      await this.updateOutputText();
      setTimeout(updateText, 500);
    };
    updateText();
  }

  async updateOutputText() {
    try {
      const response = await fetch("/get_sentence");
      const data = await response.json();
      document.getElementById("outputText").textContent =
        data.text || "Ready to sign...";
      document.getElementById("charCount").textContent = data.char_count || 0;
      document.getElementById("wordCount").textContent = data.word_count || 0;
    } catch (error) {}
  }

  async clearText() {
    try {
      await fetch("/clear_text", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });
      this.showFeedback("Cleared", "info");
      await this.updateOutputText();
    } catch (error) {}
  }

  async addSpace() {
    try {
      await fetch("/add_space", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });
      await this.updateOutputText();
    } catch (error) {}
  }

  async backspace() {
    try {
      await fetch("/backspace", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });
      await this.updateOutputText();
    } catch (error) {}
  }

  showFeedback(message, type = "info") {
    const toast = document.createElement("div");
    toast.textContent = message;
    toast.style.cssText = `position:fixed;top:55px;right:12px;background:${type === "success" ? "#5cb896" : type === "error" ? "#e8747a" : "#7c94d4"};color:#fff;padding:5px 12px;border-radius:9px;font-size:0.7rem;z-index:9999;animation:slideIn 0.2s ease;`;
    document.body.appendChild(toast);
    setTimeout(() => {
      toast.style.animation = "slideOut 0.2s ease";
      setTimeout(() => document.body.removeChild(toast), 200);
    }, 1500);
  }

  startTimeDisplay() {
    const updateTime = () => {
      const timeEl = document.getElementById("currentTime");
      if (timeEl)
        timeEl.textContent = new Date().toLocaleTimeString("en-US", {
          hour: "2-digit",
          minute: "2-digit",
        });
      setTimeout(updateTime, 1000);
    };
    updateTime();
  }

  animateConfidenceBar() {
    setInterval(() => {
      const bar = document.getElementById("confidenceBar");
      if (
        bar &&
        parseFloat(bar.style.width) === 0 &&
        this.settings.confidenceDisplay
      ) {
        bar.style.width = "3%";
        setTimeout(() => (bar.style.width = "0%"), 60);
      }
    }, 3000);
  }
}

const style = document.createElement("style");
style.textContent = `@keyframes slideIn{from{transform:translateX(100%);opacity:0}to{transform:translateX(0);opacity:1}}@keyframes slideOut{from{transform:translateX(0);opacity:1}to{transform:translateX(100%);opacity:0}}`;
document.head.appendChild(style);
document.addEventListener("DOMContentLoaded", () => {
  window.app = new SignLanguageApp();
});
