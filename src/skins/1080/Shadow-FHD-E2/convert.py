#!/usr/bin/env python3
"""Convert Shadow-FHD DreamOS skin to open Enigma2."""

import re, sys

src = open("../Shadow-FHD/skin.xml", encoding="utf-8").read()

# ── 1. Converter replacements ─────────────────────────────────────────────────

# COCEventName variants
src = re.sub(r'<convert type="COCEventName">Name[^<]*</convert>',
             '<convert type="EventName"/>', src)
src = re.sub(r'<convert type="COCEventName">FullDescription</convert>',
             '<convert type="EventName">FullDescription</convert>', src)
src = re.sub(r'<convert type="COCEventName">ExtendedDescription</convert>',
             '<convert type="EventName">ExtendedDescription</convert>', src)
src = re.sub(r'<convert type="COCEventName">Description[^<]*</convert>',
             '<convert type="EventName">ShortDescription</convert>', src)

# COCEventTime → EventTime
src = re.sub(r'<convert type="COCEventTime">Position,Negate</convert>',
             '<convert type="EventTime">Remaining</convert>\n\t\t\t\t<convert type="RemainingToText">OnlyMinutes</convert>', src)
src = re.sub(r'<convert type="COCEventTime">Remaining</convert>',
             '<convert type="EventTime">Remaining</convert>', src)
src = re.sub(r'<convert type="COCEventTime">([^<]+)</convert>',
             r'<convert type="EventTime">\1</convert>', src)

# COCClockToText → ClockToText
src = re.sub(r'<convert type="COCClockToText">',
             '<convert type="ClockToText">', src)

# COCServiceInfo → ServiceInfo
src = re.sub(r'<convert type="COCServiceInfo">',
             '<convert type="ServiceInfo">', src)

# COCConditionalShowHideLabel → ConditionalShowHide
src = re.sub(r'<convert type="COCConditionalShowHideLabel"/>',
             '<convert type="ConditionalShowHide"/>', src)

# ExtMovieInfo:Name → ServiceName:Name
src = re.sub(r'<convert type="ExtMovieInfo">Name</convert>',
             '<convert type="ServiceName">Name</convert>', src)
# ExtMovieInfo:Picon → ServiceName:Reference  (used inside render="Picon")
src = re.sub(r'<convert type="ExtMovieInfo">Picon</convert>',
             '<convert type="ServiceName">Reference</convert>', src)

# ── 2. Renderer replacements ──────────────────────────────────────────────────

# TunerLabel,N,input → Label
src = re.sub(r'render="TunerLabel,[^"]*"', 'render="Label"', src)

# ── 3. Remove widgets that use DreamOS-only renderers ─────────────────────────
# Match a full <widget ... render="RENDERER" ...> ... </widget> block (multiline)

def remove_widgets_by_renderer(text, renderer):
    # Handle both self-closing and block widgets
    # Self-closing: <widget ... render="RENDERER" .../>
    text = re.sub(
        r'<widget\b[^>]*\brender="' + re.escape(renderer) + r'"[^>]*/>', '',
        text, flags=re.DOTALL)
    # Block: <widget ... render="RENDERER" ...> ... </widget>
    text = re.sub(
        r'<widget\b[^>]*\brender="' + re.escape(renderer) + r'"[^>]*>.*?</widget>',
        '', text, flags=re.DOTALL)
    return text

for renderer in ("ExtAudioIcon", "ExtvolumeText", "Canvas", "WebView", "EventListDisplay"):
    src = remove_widgets_by_renderer(src, renderer)

# ── 4. Remove widgets using DreamOS-only converters ───────────────────────────

def remove_widgets_with_converter(text, conv_type):
    # Remove block widgets containing <convert type="CONV_TYPE">
    text = re.sub(
        r'<widget\b[^>]*/>', '', text)  # we'll handle inline below
    return text

# Remove widgets containing ExtDiskSpaceInfo, ExtCaidInfo, Extaudioinfo, DreamboxModel, InputDeviceInfo(battery), SegmentedProgress
for conv in ("ExtDiskSpaceInfo", "ExtCaidInfo", "Extaudioinfo"):
    # Remove entire <widget ...>...<convert type="CONV">...</widget> blocks
    src = re.sub(
        r'\t*<widget\b[^>]*>(?:(?!</widget>).)*?<convert type="' + re.escape(conv) + r'"[^/]*/?>(?:(?!</widget>).)*?</widget>\n?',
        '', src, flags=re.DOTALL)
    # Also self-closing widgets (unlikely but safe)
    src = re.sub(
        r'\t*<widget\b[^>]*<convert type="' + re.escape(conv) + r'"/>[^>]*/>\n?',
        '', src, flags=re.DOTALL)

# Remove DreamboxModel widget
src = re.sub(
    r'\t*<widget\b[^>]*>(?:(?!</widget>).)*?<convert type="DreamboxModel"/>(?:(?!</widget>).)*?</widget>\n?',
    '', src, flags=re.DOTALL)

# Remove InputDeviceInfo widgets (DreamOS BT-remote specific)
src = re.sub(
    r'\t*<widget\b[^>]*>(?:(?!</widget>).)*?<convert type="InputDeviceInfo"[^/]*/?>(?:(?!</widget>).)*?</widget>\n?',
    '', src, flags=re.DOTALL)

# Replace SegmentedProgress with nothing (remove the convert line)
src = re.sub(r'\s*<convert type="SegmentedProgress">[^<]*</convert>', '', src)

# ── 5. Remove DreamOS-specific source/attributes ──────────────────────────────

# Remove HbbtvApplication widgets
src = re.sub(
    r'\t*<widget\b[^>]*\bsource="HbbtvApplication"[^>]*>(?:(?!</widget>).)*?</widget>\n?',
    '', src, flags=re.DOTALL)
src = re.sub(
    r'\t*<widget\b[^>]*\bsource="HbbtvApplication"[^>]*/>\n?',
    '', src, flags=re.DOTALL)

# Remove selectionZoom attribute
src = re.sub(r'\s+selectionZoom="[^"]*"', '', src)

# Remove mode="grid" attribute (revert to standard listbox mode)
src = re.sub(r'\s+mode="grid"', '', src)

# Remove margin="..." on Listbox
src = re.sub(r'\s+margin="[^"]*"', '', src)

# Remove backgroundPixmap attribute on Listbox (DreamOS grid background)
src = re.sub(r'\s+backgroundPixmap="[^"]*"', '', src)

# Remove selectionPixmap attribute - actually keep this, it's standard E2
# src = re.sub(r'\s+selectionPixmap="[^"]*"', '', src)

# ── 6. Remove WindowDimmer windowstyle entry (DreamOS-only eWindowStyleSkinned slot) ──
src = re.sub(r'\s*<color color="[^"]*" name="WindowDimmer"/>', '', src)

# ── 7. Make skin self-contained: repoint all Shadow-FHD/ asset paths ─────────
# Replace all Shadow-FHD/ path references with Shadow-FHD-E2/
src = src.replace('Shadow-FHD/', 'Shadow-FHD-E2/')
# Fix multi-pixmap rc widget: subsequent entries lack the skin prefix
src = re.sub(r'(rc\d\.png),skin_default/', r'\1,Shadow-FHD-E2/skin_default/', src)

# ── 8. Clean up empty lines left by removals ─────────────────────────────────
src = re.sub(r'\n{3,}', '\n\n', src)

# ── 9. Write output ──────────────────────────────────────────────────────────
open("skin.xml", "w", encoding="utf-8").write(src)
print("Done. Lines:", src.count('\n'))
