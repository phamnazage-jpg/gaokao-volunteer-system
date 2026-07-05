from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Union

from PIL import Image, ImageDraw, ImageFont

from data.orders.masking import mask_name
from data.share.short_link import build_url

POSTER_SIZE = (1080, 1920)
_QR_SIZE = 276
_PADDING_X = 72
_CARD_GAP = 24
_CARD_RADIUS = 28

_FONT_CANDIDATES = {
    "regular": [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansSC-Regular.ttf",
    ],
    "bold": [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansSC-Bold.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
    ],
}


@dataclass(frozen=True)
class PosterRecommendation:
    school: str
    major: str
    probability: str


@dataclass(frozen=True)
class PosterPayload:
    report_id: str
    title: str
    candidate_name: str = ""
    score_line: str = ""
    recommendations: list[PosterRecommendation] = field(default_factory=list)
    share_url: str = ""
    footer_note: str = "Powered by 龙老师"


@dataclass(frozen=True)
class PosterRenderResult:
    output_path: Path
    format: str
    size: tuple[int, int]


@dataclass(frozen=True)
class _FontBundle:
    title: Union[ImageFont.FreeTypeFont, ImageFont.ImageFont]
    subtitle: Union[ImageFont.FreeTypeFont, ImageFont.ImageFont]
    body: Union[ImageFont.FreeTypeFont, ImageFont.ImageFont]
    small: Union[ImageFont.FreeTypeFont, ImageFont.ImageFont]
    brand: Union[ImageFont.FreeTypeFont, ImageFont.ImageFont]


@dataclass(frozen=True)
class _Box:
    x0: int
    y0: int
    x1: int
    y1: int

    @property
    def width(self) -> int:
        return self.x1 - self.x0

    @property
    def height(self) -> int:
        return self.y1 - self.y0


def build_poster_payload(
    report: dict[str, Any],
    *,
    code: str,
    share_url: str | None = None,
    mask_name_value: bool = True,
) -> PosterPayload:
    report_id = str(report.get("report_id") or code)
    title = str(report.get("title") or "高考志愿填报方案")
    candidate_raw = str(report.get("candidate_name") or report.get("name") or "考生")
    candidate_name = str(mask_name(candidate_raw) if mask_name_value else candidate_raw)
    score_value = report.get("score")
    score_text = (
        f"{score_value}分"
        if score_value is not None and str(score_value).strip() != ""
        else "分数待补充"
    )
    score_bits = [
        score_text,
        str(report.get("province") or "省份待补充"),
        str(report.get("year") or "2026"),
    ]
    score_line = " · ".join(bit for bit in score_bits if bit)
    recommendations = _normalize_recommendations(report.get("recommendations"))[:3]
    payload = [
        PosterRecommendation(
            school=item.get("school") or item.get("university") or "院校待补充",
            major=item.get("major") or item.get("program") or "专业待补充",
            probability=_format_probability(item.get("prob")),
        )
        for item in recommendations
    ]
    if not payload:
        payload = [
            PosterRecommendation(
                school="院校待补充",
                major="专业待补充",
                probability="待评估",
            )
        ]
    return PosterPayload(
        report_id=report_id,
        title=title,
        candidate_name=candidate_name,
        score_line=score_line,
        recommendations=payload,
        share_url=share_url or build_url(code, base="http://localhost:8000"),
    )


def save_poster(
    report: dict[str, Any],
    *,
    code: str,
    share_url: str | None,
    output_path: str | Path,
    mask_name: bool = True,
) -> PosterRenderResult:
    payload = build_poster_payload(
        report,
        code=code,
        share_url=share_url,
        mask_name_value=mask_name,
    )
    image = render_poster(payload)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fmt = _detect_format(path)
    if fmt == "JPEG":
        image.convert("RGB").save(path, format=fmt, quality=92)
    else:
        image.save(path, format=fmt, optimize=True)
    return PosterRenderResult(output_path=path, format=fmt, size=image.size)


def render_poster(payload: PosterPayload) -> Image.Image:
    canvas = Image.new("RGB", POSTER_SIZE, "#f4f7fb")
    draw = ImageDraw.Draw(canvas)
    fonts = _load_fonts()

    _draw_header(draw, fonts, payload)
    _draw_candidate_summary(draw, fonts, payload)
    _draw_recommendations(draw, fonts, payload)
    _draw_qr_section(canvas, draw, fonts, payload)
    _draw_footer(draw, fonts, payload)
    return canvas


def _draw_header(
    draw: ImageDraw.ImageDraw, fonts: _FontBundle, payload: PosterPayload
) -> None:
    box = _Box(_PADDING_X, 64, POSTER_SIZE[0] - _PADDING_X, 420)
    draw.rounded_rectangle((box.x0, box.y0, box.x1, box.y1), radius=36, fill="#194fb6")
    draw.text(
        (box.x0 + 42, box.y0 + 44), "高考志愿填报方案", font=fonts.brand, fill="#dbeafe"
    )
    title_lines = _wrap_text(draw, payload.title, fonts.title, box.width - 84)
    title_y = box.y0 + 114
    for line in title_lines[:2]:
        draw.text((box.x0 + 42, title_y), line, font=fonts.title, fill="#ffffff")
        title_y += _line_height(draw, fonts.title, line) + 10
    draw.text(
        (box.x0 + 42, box.y1 - 78),
        f"报告ID：{payload.report_id}",
        font=fonts.small,
        fill="#dbeafe",
    )


def _draw_candidate_summary(
    draw: ImageDraw.ImageDraw, fonts: _FontBundle, payload: PosterPayload
) -> None:
    box = _Box(_PADDING_X, 456, POSTER_SIZE[0] - _PADDING_X, 640)
    draw.rounded_rectangle(
        (box.x0, box.y0, box.x1, box.y1), radius=_CARD_RADIUS, fill="#ffffff"
    )
    draw.text(
        (box.x0 + 34, box.y0 + 28), "考生信息", font=fonts.subtitle, fill="#172033"
    )
    draw.text(
        (box.x0 + 34, box.y0 + 82),
        f"考生：{payload.candidate_name}",
        font=fonts.body,
        fill="#1e293b",
    )
    score_lines = _wrap_text(draw, payload.score_line, fonts.body, box.width - 68)
    y = box.y0 + 124
    for line in score_lines[:2]:
        draw.text((box.x0 + 34, y), line, font=fonts.body, fill="#4b5563")
        y += _line_height(draw, fonts.body, line) + 8


def _draw_recommendations(
    draw: ImageDraw.ImageDraw, fonts: _FontBundle, payload: PosterPayload
) -> None:
    start_y = 692
    draw.text(
        (_PADDING_X, start_y), "推荐院校 TOP3", font=fonts.subtitle, fill="#172033"
    )
    card_top = start_y + 52
    card_height = 146
    for idx, rec in enumerate(payload.recommendations[:3], start=1):
        top = card_top + (idx - 1) * (card_height + _CARD_GAP)
        box = _Box(_PADDING_X, top, POSTER_SIZE[0] - _PADDING_X, top + card_height)
        draw.rounded_rectangle(
            (box.x0, box.y0, box.x1, box.y1), radius=_CARD_RADIUS, fill="#ffffff"
        )
        badge_box = (box.x0 + 26, box.y0 + 30, box.x0 + 94, box.y0 + 92)
        draw.rounded_rectangle(badge_box, radius=22, fill="#e0ecff")
        draw.text(
            (box.x0 + 48, box.y0 + 44),
            str(idx),
            font=fonts.subtitle,
            fill="#194fb6",
            anchor="mm",
        )
        draw.text(
            (box.x0 + 120, box.y0 + 30), rec.school, font=fonts.body, fill="#172033"
        )
        draw.text(
            (box.x0 + 120, box.y0 + 78), rec.major, font=fonts.small, fill="#5b6b88"
        )
        prob_text = rec.probability
        prob_bbox = draw.textbbox((0, 0), prob_text, font=fonts.body)
        prob_x = box.x1 - (prob_bbox[2] - prob_bbox[0]) - 34
        draw.text((prob_x, box.y0 + 54), prob_text, font=fonts.body, fill="#0f766e")


def _draw_qr_section(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    fonts: _FontBundle,
    payload: PosterPayload,
) -> None:
    box = _Box(_PADDING_X, 1248, POSTER_SIZE[0] - _PADDING_X, 1760)
    draw.rounded_rectangle(
        (box.x0, box.y0, box.x1, box.y1), radius=_CARD_RADIUS, fill="#ffffff"
    )
    draw.text(
        (box.x0 + 34, box.y0 + 28),
        "扫码查看完整方案",
        font=fonts.subtitle,
        fill="#172033",
    )
    draw.text(
        (box.x0 + 34, box.y0 + 78), payload.share_url, font=fonts.small, fill="#5b6b88"
    )
    qr = _make_qr_image(payload.share_url)
    qr_x = box.x0 + (box.width - qr.width) // 2
    qr_y = box.y0 + 136
    canvas.paste(qr, (qr_x, qr_y))
    draw.text(
        (box.x0 + box.width // 2, qr_y + qr.height + 28),
        "微信扫码或长按识别二维码",
        font=fonts.body,
        fill="#334155",
        anchor="ma",
    )


def _draw_footer(
    draw: ImageDraw.ImageDraw, fonts: _FontBundle, payload: PosterPayload
) -> None:
    footer_y = 1822
    draw.text(
        (_PADDING_X, footer_y), payload.footer_note, font=fonts.body, fill="#194fb6"
    )
    draw.text(
        (_PADDING_X, footer_y + 42),
        "本海报仅供沟通参考，最终请以正式报告与考试院信息为准。",
        font=fonts.small,
        fill="#64748b",
    )


def _normalize_recommendations(raw: Any) -> list[dict[str, Any]]:
    if not isinstance(raw, list):
        return []
    out: list[dict[str, Any]] = []
    for item in raw:
        if isinstance(item, dict):
            out.append(item)
    return out


def _format_probability(value: Any) -> str:
    if value is None or value == "":
        return "待评估"
    if isinstance(value, (int, float)):
        return f"{int(round(float(value)))}%"
    return str(value)


def _load_font(
    size: int, *, weight: str
) -> Union[ImageFont.FreeTypeFont, ImageFont.ImageFont]:
    for candidate in _FONT_CANDIDATES[weight]:
        path = Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def _load_fonts() -> _FontBundle:
    return _FontBundle(
        title=_load_font(56, weight="bold"),
        subtitle=_load_font(34, weight="bold"),
        body=_load_font(30, weight="regular"),
        small=_load_font(22, weight="regular"),
        brand=_load_font(24, weight="bold"),
    )


def _wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: Union[ImageFont.FreeTypeFont, ImageFont.ImageFont],
    max_width: int,
) -> list[str]:
    words = list(_iter_text_units(text))
    if not words:
        return [""]
    lines: list[str] = []
    current = ""
    for unit in words:
        candidate = current + unit
        if current and _text_width(draw, candidate, font) > max_width:
            lines.append(current.rstrip())
            current = unit.lstrip()
        else:
            current = candidate
    if current:
        lines.append(current.rstrip())
    return lines or [text]


def _iter_text_units(text: str) -> Iterable[str]:
    if " " in text:
        parts = text.split(" ")
        for idx, part in enumerate(parts):
            yield part + (" " if idx < len(parts) - 1 else "")
        return
    for char in text:
        yield char


def _text_width(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: Union[ImageFont.FreeTypeFont, ImageFont.ImageFont],
) -> int:
    left, _, right, _ = draw.textbbox((0, 0), text, font=font)
    return int(right - left)


def _line_height(
    draw: ImageDraw.ImageDraw,
    font: Union[ImageFont.FreeTypeFont, ImageFont.ImageFont],
    sample: str,
) -> int:
    _, top, _, bottom = draw.textbbox((0, 0), sample or "Hg", font=font)
    return int(bottom - top)


def _make_qr_image(content: str) -> Image.Image:
    try:
        import qrcode  # type: ignore[import-untyped]
    except ImportError as exc:  # pragma: no cover - exercised in CLI/runtime only
        raise RuntimeError("缺少 qrcode 依赖，请先安装 requirements-admin.txt") from exc

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(content)
    qr.make(fit=True)
    image = qr.make_image(fill_color="black", back_color="white")
    if hasattr(image, "get_image"):
        image = image.get_image()
    if not isinstance(image, Image.Image):
        raise RuntimeError("qrcode 未返回 Pillow 图像")
    return image.convert("RGB").resize((_QR_SIZE, _QR_SIZE))


def _detect_format(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".jpg", ".jpeg"}:
        return "JPEG"
    return "PNG"
