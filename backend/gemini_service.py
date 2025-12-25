"""
Gemini AI Service untuk Trading Chatbot
Integrasi dengan Google Gemini API untuk analisis pasar crypto
"""

import google.generativeai as genai
from typing import Dict, List, Optional
from pathlib import Path
import json
import os

# Path untuk menyimpan konfigurasi
CONFIG_DIR = Path(__file__).parent
API_KEY_FILE = CONFIG_DIR / ".api_key"
MODEL_CONFIG_FILE = CONFIG_DIR / ".model_config"

# Available models with info
AVAILABLE_MODELS = {
    "gemini-3-pro-preview": {
        "name": "Gemini 3 Pro (Preview)",
        "description": "Latest & most powerful, advanced reasoning",
        "tier": "preview"
    },
    "gemini-3-flash-preview": {
        "name": "Gemini 3 Flash (Preview)",
        "description": "Fast with Pro-level intelligence",
        "tier": "preview"
    },
    "gemini-2.5-flash": {
        "name": "Gemini 2.5 Flash (Stable)",
        "description": "Best price-performance, stable",
        "tier": "stable"
    },
    "gemini-2.5-pro": {
        "name": "Gemini 2.5 Pro (Stable)",
        "description": "Advanced reasoning, stable",
        "tier": "stable"
    },
    "gemini-2.0-flash": {
        "name": "Gemini 2.0 Flash (Stable)",
        "description": "Fast model from previous generation",
        "tier": "stable"
    },
}

DEFAULT_MODEL = "gemini-2.5-flash"


def get_api_key() -> Optional[str]:
    """Read API key from environment variable or file"""
    # 1. Check environment variable first (for production)
    env_key = os.environ.get('GEMINI_API_KEY')
    if env_key:
        return env_key
    # 2. Fallback to file (for local development)
    if API_KEY_FILE.exists():
        key = API_KEY_FILE.read_text().strip()
        if key:
            return key
    return None


def save_api_key(api_key: str) -> bool:
    """Save API key to file"""
    try:
        API_KEY_FILE.write_text(api_key.strip())
        return True
    except Exception:
        return False


def get_selected_model() -> str:
    """Read selected model from file"""
    if MODEL_CONFIG_FILE.exists():
        try:
            config = json.loads(MODEL_CONFIG_FILE.read_text())
            model = config.get("model", DEFAULT_MODEL)
            if model in AVAILABLE_MODELS:
                return model
        except Exception:
            pass
    return DEFAULT_MODEL


def save_selected_model(model: str) -> bool:
    """Save selected model to file"""
    try:
        if model not in AVAILABLE_MODELS:
            return False
        config = {"model": model}
        MODEL_CONFIG_FILE.write_text(json.dumps(config))
        return True
    except Exception:
        return False


def get_available_models() -> Dict:
    """Return list of available models"""
    return AVAILABLE_MODELS


def validate_api_key(api_key: str, model: str = None) -> Dict:
    """Validate API key by trying a simple request"""
    if model is None:
        model = get_selected_model()

    try:
        genai.configure(api_key=api_key)
        test_model = genai.GenerativeModel(model)
        # Test dengan prompt minimal
        response = test_model.generate_content("Hi")
        if response.text:
            return {"valid": True, "error": None}
        return {"valid": False, "error": "empty_response"}
    except Exception as e:
        error_msg = str(e).lower()
        if "api_key" in error_msg or "invalid" in error_msg or "401" in error_msg:
            return {"valid": False, "error": "invalid_api_key"}
        elif "quota" in error_msg or "rate" in error_msg or "429" in error_msg:
            return {"valid": False, "error": "rate_limit"}
        elif "not found" in error_msg or "404" in error_msg:
            return {"valid": False, "error": "model_not_found"}
        else:
            return {"valid": False, "error": str(e)}


class GeminiService:
    def __init__(self):
        self.api_key = get_api_key()
        self.model_name = get_selected_model()
        self.model = None

        if self.api_key:
            self._init_model()

    def _init_model(self):
        """Initialize model with current settings"""
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
        except Exception as e:
            print(f"Warning: Failed to initialize Gemini: {e}")
            self.model = None

    def is_configured(self) -> bool:
        """Check if API key is configured"""
        return self.api_key is not None and self.model is not None

    def get_current_model(self) -> str:
        """Return currently used model"""
        return self.model_name

    def set_model(self, model: str) -> bool:
        """Change model to use"""
        if model not in AVAILABLE_MODELS:
            return False

        self.model_name = model
        save_selected_model(model)

        if self.api_key:
            self._init_model()

        return True

    def reload_api_key(self):
        """Reload API key dari file"""
        self.api_key = get_api_key()
        self.model_name = get_selected_model()
        if self.api_key:
            self._init_model()

    def _build_system_prompt(self, market_data: Dict, timeframe: str) -> str:
        """Build system prompt dengan konteks data pasar"""

        signals = market_data.get('signals', [])
        total_coins = len(signals)

        # Calculate RSI distribution
        overbought = [s for s in signals if s.get('rsi', 0) >= 70]
        oversold = [s for s in signals if s.get('rsi', 0) <= 30]

        # Calculate signal layers
        long_l5 = [s for s in signals if s.get('long_layer', 0) == 5]
        long_l4 = [s for s in signals if s.get('long_layer', 0) == 4]
        short_l5 = [s for s in signals if s.get('short_layer', 0) == 5]
        short_l4 = [s for s in signals if s.get('short_layer', 0) == 4]

        # Format top signals
        def format_signal(s):
            return f"  - {s['symbol']}: RSI={s.get('rsi', 0):.1f}, Layer={s.get('long_layer', 0) or s.get('short_layer', 0)}"

        # Sort by layer strength
        top_long = sorted(
            [s for s in signals if s.get('long_layer', 0) >= 3],
            key=lambda x: (-x.get('long_layer', 0), x.get('rsi', 50))
        )[:5]

        top_short = sorted(
            [s for s in signals if s.get('short_layer', 0) >= 3],
            key=lambda x: (-x.get('short_layer', 0), -x.get('rsi', 50))
        )[:5]

        top_long_str = "\n".join([format_signal(s) for s in top_long]) if top_long else "  Tidak ada signal kuat"
        top_short_str = "\n".join([format_signal(s) for s in top_short]) if top_short else "  Tidak ada signal kuat"

        system_prompt = f"""Kamu adalah asisten analis pasar crypto untuk aplikasi Crypto Heatmap.
Kamu membantu trader menganalisis kondisi pasar berdasarkan data RSI dan EMA.

DATA PASAR SAAT INI (Timeframe: {timeframe}):
- Total koin dianalisis: {total_coins}
- Signal LONG kuat (L4-L5): {len(long_l4) + len(long_l5)} koin
- Signal SHORT kuat (L4-L5): {len(short_l4) + len(short_l5)} koin

DISTRIBUSI RSI:
- Overbought (RSI > 70): {len(overbought)} koin
- Oversold (RSI < 30): {len(oversold)} koin

TOP SIGNAL LONG (Buy):
{top_long_str}

TOP SIGNAL SHORT (Sell):
{top_short_str}

PENJELASAN SIGNAL LAYER:
- Layer 5: EMA cross + RSI extreme + Smoothed RSI cross + Divergence (TERKUAT)
- Layer 4: EMA cross + RSI extreme + Divergence
- Layer 3: RSI extreme + Smoothed RSI cross
- Layer 2: RSI extreme + Divergence
- Layer 1: Hanya EMA cross + retest

PANDUAN RESPON:
1. Jawab dengan bahasa Indonesia yang jelas dan ringkas
2. Selalu sebutkan data spesifik (symbol, RSI, layer) saat memberikan analisis
3. Berikan insight yang actionable berdasarkan data
4. PENTING: Selalu ingatkan bahwa ini bukan financial advice

Jawab pertanyaan user berdasarkan data di atas."""

        return system_prompt

    async def generate_response(
        self,
        user_message: str,
        market_data: Dict,
        timeframe: str = "4h",
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict:
        """Generate AI response based on user message and market data"""

        if not self.is_configured():
            return {
                "success": False,
                "response": "API key not configured. Please enter your Gemini API key in settings.",
                "error": "not_configured"
            }

        try:
            system_prompt = self._build_system_prompt(market_data, timeframe)

            # Build chat history
            messages = []

            # Add conversation history if exists
            if conversation_history:
                for msg in conversation_history[-6:]:  # Last 6 messages for context
                    role = "user" if msg.get("role") == "user" else "model"
                    messages.append({
                        "role": role,
                        "parts": [msg.get("content", "")]
                    })

            # Create chat with system instruction
            chat = self.model.start_chat(history=messages)

            # Combine system prompt with user message for first message
            full_prompt = f"{system_prompt}\n\nPertanyaan User: {user_message}"

            # Generate response
            response = chat.send_message(full_prompt)

            return {
                "success": True,
                "response": response.text,
                "error": None
            }

        except Exception as e:
            error_msg = str(e).lower()

            # Handle specific errors with clear messages
            if "api_key" in error_msg or "invalid" in error_msg or "401" in error_msg or "api key not valid" in error_msg:
                return {
                    "success": False,
                    "response": "Invalid API key. Please check and enter the correct API key in settings.",
                    "error": "invalid_api_key"
                }
            elif "quota" in error_msg or "rate" in error_msg or "429" in error_msg or "resource" in error_msg:
                return {
                    "success": False,
                    "response": "API usage limit reached. Gemini free tier has a limit of 15 requests/minute. Please wait and try again.",
                    "error": "rate_limit"
                }
            elif "not found" in error_msg or "404" in error_msg:
                return {
                    "success": False,
                    "response": f"Model '{self.model_name}' not found or not available. Try selecting a different model in settings.",
                    "error": "model_not_found"
                }
            elif "permission" in error_msg or "403" in error_msg:
                return {
                    "success": False,
                    "response": "API key does not have permission to access Gemini. Make sure the API key is activated.",
                    "error": "permission_denied"
                }
            else:
                return {
                    "success": False,
                    "response": f"An error occurred: {str(e)}",
                    "error": "unknown"
                }

    def get_market_summary(self, market_data: Dict) -> Dict:
        """Generate market summary from heatmap data"""

        signals = market_data.get('signals', [])

        overbought_count = len([s for s in signals if s.get('rsi', 0) >= 70])
        oversold_count = len([s for s in signals if s.get('rsi', 0) <= 30])

        strong_long = len([s for s in signals if s.get('long_layer', 0) >= 4])
        strong_short = len([s for s in signals if s.get('short_layer', 0) >= 4])

        return {
            "total_coins": len(signals),
            "overbought_count": overbought_count,
            "oversold_count": oversold_count,
            "strong_long_signals": strong_long,
            "strong_short_signals": strong_short
        }

    async def generate_fundamental_analysis(
        self,
        symbol: str,
        timeframe: str = "4h"
    ) -> Dict:
        """Generate AI-powered fundamental analysis for a specific coin

        Uses Gemini 3 Flash specifically for this feature.
        """

        # Use Gemini 3 Flash specifically for fundamental analysis
        FUNDAMENTAL_MODEL = "gemini-3-flash-preview"

        if not self.api_key:
            return {
                "success": False,
                "response": "API key not configured. Please enter your Gemini API key in settings.",
                "error": "not_configured"
            }

        try:
            # Create a dedicated model instance for fundamental analysis
            genai.configure(api_key=self.api_key)
            fundamental_model = genai.GenerativeModel(FUNDAMENTAL_MODEL)

            system_prompt = f"""You are a crypto fundamental analyst. Provide a comprehensive fundamental analysis for {symbol}.

Structure your response with these sections:

## 1. INTRINSIC VALUE
- Token supply model (fixed supply like BTC's 21M, or inflationary)
- Primary use case and underlying technology
- Team/Founder background and credibility

## 2. MACROECONOMIC FACTORS
- Impact of current interest rate environment
- Regulatory landscape and recent developments
- Overall crypto market sentiment

## 3. COIN-SPECIFIC EVENTS
- Upcoming token unlocks or vesting schedules
- ETF approvals/applications (if applicable)
- Protocol upgrades or major releases
- Recent partnership announcements

Keep the analysis concise but informative. Use bullet points for clarity.
Timeframe context: {timeframe}

IMPORTANT: End with a disclaimer that this is not financial advice."""

            # Generate response using Gemini 3 Flash
            response = fundamental_model.generate_content(system_prompt)

            return {
                "success": True,
                "response": response.text,
                "error": None
            }

        except Exception as e:
            error_msg = str(e).lower()

            if "api_key" in error_msg or "invalid" in error_msg or "401" in error_msg:
                return {
                    "success": False,
                    "response": "Invalid API key. Please check and enter the correct API key in settings.",
                    "error": "invalid_api_key"
                }
            elif "quota" in error_msg or "rate" in error_msg or "429" in error_msg:
                return {
                    "success": False,
                    "response": "API usage limit reached. Please wait and try again.",
                    "error": "rate_limit"
                }
            elif "not found" in error_msg or "404" in error_msg:
                return {
                    "success": False,
                    "response": f"Model '{FUNDAMENTAL_MODEL}' not found. This may be a preview model not available in your region.",
                    "error": "model_not_found"
                }
            else:
                return {
                    "success": False,
                    "response": f"An error occurred: {str(e)}",
                    "error": "unknown"
                }
