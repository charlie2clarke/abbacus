import logging
import os
from configparser import ConfigParser
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

DEFAULT_CFG_PATH = Path.home().joinpath(".abbacus", "config.ini")


class UninitialisedException(Exception):
    def __init__(
        self,
        message="Cfg has not been initialised. The first call must specify the input parameter which is the filepath to the config file.",
    ):
        self.message = message
        super().__init__(self.message)


@dataclass
class CfgOpt:
    name: str
    value: str
    _type: type
    _default_off: str


class Cfg(object):
    opts: Dict[CfgOpt]
    _DEFAULT_OPTS = [
        CfgOpt(name="headings", value="True", _default_off="False", _type=bool),
        CfgOpt(name="titles", value="True", _default_off="False", _type=bool),
        CfgOpt(name="subtitles", value="True", _default_off="False", _type=bool),
        CfgOpt(name="captions", value="True", _default_off="False", _type=bool),
        CfgOpt(name="figures", value="True", _default_off="False", _type=bool),
        CfgOpt(
            name="ignored_sections",
            value='["Appendices", "Appendix", "Bibliography", "References", "Works Cited"]',
            _default_off="[]",
            _type=list(str),
        ),
    ]
    _DEFAULT_SECT = "DEFAULT"
    _instance = None
    _input = None

    def __new__(cls, input: str = str(DEFAULT_CFG_PATH)):
        if cls._instance is None:
            cls._instance = super(Cfg, cls).__new__(cls)
            cls._input = input or str(DEFAULT_CFG_PATH)
            cfg = cls._instance._load_cfg()
            cls._instance._init_opts(cfg)

        if cls._instance is None and cls._input is None:
            raise UninitialisedException()
        return cls._instance

    def _init_opts(self, cfg: ConfigParser) -> None:
        for opt, value in cfg.items():
            self.opts[opt] = CfgOpt(name=opt, value=value)
        if self.opts is None:
            raise UninitialisedException()

    def _default_cfg(self) -> ConfigParser:
        cfg = ConfigParser()
        for opt in self._DEFAULT_OPTS:
            cfg.set(self._DEFAULT_SECT, opt.name, opt.value)
        return cfg

    def _write_default_cfg(self) -> ConfigParser:
        cfg = self.default_cfg(cfg)
        dir = os.path.dirname(self._input)

        try:
            if not os.path.exists(dir):
                os.makedirs(dir)

            with open(self._input, "w") as config_file:
                cfg.write(config_file)

            logging.info(f"Default configuration created at {self._input}")
            return cfg
        except Exception as e:
            raise Exception(
                f"An error occurred while writing the default configuration: {e}"
            )

    def _read_existing_cfg(self) -> ConfigParser:
        cfg = ConfigParser()
        cfg.read(self._input)

        for opt in self._DEFAULT_OPTS:
            if not cfg.has_option(self._DEFAULT_SECT, opt.name):
                logging.info(
                    f"{opt.name} not found in config, defaulting to off value: {opt._default_off}"
                )
                cfg.set(self._DEFAULT_SECT, opt.name, opt._default_off)
            else:
                value = cfg.get(self._DEFAULT_SECT, opt.name)
                if value is not None:
                    try:
                        if opt._type == bool:
                            if value.lower() not in ["true", "false"]:
                                raise ValueError
                        else:
                            opt._type(value)
                    except ValueError:
                        logging.warn(
                            f"Invalid value set for {opt.name}, defaulting to off: {opt._default_off}"
                        )
                        cfg.set(self._DEFAULT_SECT, opt.name, opt._default_off)

        logging.info(
            "Read config. Running with the following:\n{}".format(
                "\n".join(
                    f"{opt}: {value}" for opt, value in cfg.items(self._DEFAULT_SECT)
                )
            )
        )
        return cfg

    def _load_cfg(self) -> ConfigParser:
        is_file = os.path.isfile(self._input)

        if not is_file and self._input != str(DEFAULT_CFG_PATH):
            raise Exception(f"File {self._input} not found")

        if not is_file:
            logging.info("Writing a new default config")
            return self._write_default_cfg()

        logging.info("Reading config")
        return self._read_existing_cfg()