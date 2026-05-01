import json
import os
from importlib import resources
from typing import Dict, Any, Optional

class BaziConfig:
    def __init__(self, config_path: str = "data/latlng.json"):
        self.config_path = config_path
        self.flat_latlng: Dict[str, float] = {}
        self._load_config()

    def _load_config(self):
        if not os.path.exists(self.config_path):
            self._load_packaged_config()
            return

        with open(self.config_path, "r", encoding="utf-8") as f:
            self._load_json(f, self.config_path)

    def _load_packaged_config(self):
        try:
            config_file = resources.files("src.engine.data").joinpath("latlng.json")
            with config_file.open("r", encoding="utf-8") as f:
                self._load_json(f, str(config_file))
        except FileNotFoundError:
            return

    def _load_json(self, f, source: str):
        try:
            data = json.load(f)
            self._flatten_data(data)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"地名数据文件 {source} 解析失败: {e}") from e

    def _flatten_data(self, item: Any):
        """
        递归地将树形结构的城市数据扁平化。
        注意：观察 data/latlng.json 发现 'lat' 字段存的是经度 (116.40...)，
        'lng' 字段存的是纬度 (39.90...)。我们需要经度进行真太阳时校正。
        """
        if isinstance(item, dict):
            name = item.get("name")
            # 这里的 'lat' 实际上存储的是经度数据（如北京 116.40）
            lon_str = item.get("lat")
            if name and lon_str:
                try:
                    self.flat_latlng[name] = float(lon_str)
                except ValueError:
                    pass
            
            # 递归处理子节点
            children = item.get("children", [])
            for child in children:
                self._flatten_data(child)
        elif isinstance(item, list):
            for sub_item in item:
                self._flatten_data(sub_item)

    def get_longitude(self, location: str) -> float:
        """
        根据地名获取经度。精确匹配优先，失败后依次追加"市/区/县/省"后缀重试。
        仍找不到则抛出 ValueError，不做静默 fallback。
        """
        if location in self.flat_latlng:
            return self.flat_latlng[location]
        for suffix in ("市", "区", "县", "省"):
            candidate = location + suffix
            if candidate in self.flat_latlng:
                return self.flat_latlng[candidate]
        available = "、".join(sorted(self.flat_latlng.keys())[:10]) + " …"
        raise ValueError(f"找不到地名 '{location}'，请输入完整地名，例如：{available}")

# 创建默认配置实例
config = BaziConfig()
