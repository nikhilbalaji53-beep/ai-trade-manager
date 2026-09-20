from typing import Dict, List, Any, Optional

from app.services.instrument_master import get_all_instruments, get_instrument_by_symbol, search_instruments


class InstrumentManager:
    """
    Instrument Master Manager:
    Provides dynamic loading, mapping, and lookup of Indian Stock Market instruments across NSE & BSE.
    Supports symbol mapping formats:
    - NSE:RELIANCE
    - NSE:TCS
    - NSE:NIFTY50 / NSE:NIFTY 50
    - NSE:NIFTYBANK / NSE:NIFTY BANK
    - BSE:SENSEX
    """

    def __init__(self):
        self._instruments: Dict[str, Dict[str, Any]] = {}
        self.load_instruments()

    def load_instruments(self):
        catalog = get_all_instruments()
        for inst in catalog:
            sym = inst["symbol"].upper()
            exch = inst["exchange"].upper()
            key_plain = sym
            key_colon = f"{exch}:{sym}"
            key_spaceless = sym.replace(" ", "")
            key_colon_spaceless = f"{exch}:{key_spaceless}"

            self._instruments[key_plain] = inst
            self._instruments[key_colon] = inst
            self._instruments[key_spaceless] = inst
            self._instruments[key_colon_spaceless] = inst

            if exch == "NSE":
                self._instruments[f"{sym}.NS"] = inst
            elif exch == "BSE":
                self._instruments[f"{sym}.BO"] = inst

    def get_instrument(self, symbol_or_identifier: str) -> Optional[Dict[str, Any]]:
        clean = symbol_or_identifier.strip().upper()
        if clean in self._instruments:
            return self._instruments[clean]

        # Strip exchange prefixes and extensions
        stripped = (
            clean.replace("NSE:", "")
            .replace("BSE:", "")
            .replace("NASDAQ:", "")
            .replace("NYSE:", "")
            .replace("CBOE:", "")
            .replace(".NS", "")
            .replace(".BO", "")
            .strip()
        )
        if stripped in self._instruments:
            return self._instruments[stripped]
        stripped_nospace = stripped.replace(" ", "")
        return self._instruments.get(stripped_nospace)

    def get_instrument_token(self, symbol: str) -> Optional[int]:
        inst = self.get_instrument(symbol)
        return inst.get("instrument_token") if inst else None

    def get_instrument_by_token(self, token: Any) -> Optional[Dict[str, Any]]:
        try:
            tok_int = int(token)
            for inst in get_all_instruments():
                if inst.get("instrument_token") == tok_int:
                    return inst
        except (ValueError, TypeError):
            pass
        return None

    def get_all(self) -> List[Dict[str, Any]]:
        return get_all_instruments()

    def search(self, query: str) -> List[Dict[str, Any]]:
        from app.services.instrument_master import search_instruments
        return search_instruments(query)

    def search_advanced(
        self,
        query: Optional[str] = None,
        market: Optional[str] = None,
        exchange: Optional[str] = None,
        segment: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        from app.services.instrument_master import search_instruments_advanced
        return search_instruments_advanced(query, market, exchange, segment, limit)


_instrument_manager = InstrumentManager()


def get_instrument_manager() -> InstrumentManager:
    return _instrument_manager

