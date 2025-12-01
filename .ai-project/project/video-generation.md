# Video Generation Workflow

This document describes how to keep slides and videos in sync.

## Overview

The presentation video is generated from:
1. **Slides** - Marp markdown (`presentation.md`) → PNG images
2. **Narration** - JSON file (`scripts/slide-narrations.json`) → Audio via TTS
3. **Video** - Combine slides + audio → Final MP4

## Files

| File | Purpose |
|------|---------|
| `presentation.md` | Marp slides source (markdown) |
| `scripts/slide-narrations.json` | Narration text per slide |
| `scripts/generate-video.py` | Local video generation script |
| `assets/slides/slide.NNN.png` | Generated slide images |
| `assets/presentation-video.mp4` | Final output video |

---

## Style Guide

### Slide Composition

**Keep slides minimal:**
- 10-20 words maximum per slide
- Use concise bullet points
- Let visuals do the heavy lifting

**Visual elements to include:**
- ASCII diagrams for workflows and architecture
- Code snippets for technical concepts
- Tables for comparisons and data
- Bar charts using Unicode blocks (█)

**Formatting:**
```markdown
## Main Point

```
ASCII diagram or code here
```

*Brief caption*
```

**Avoid:**
- Walls of text
- Repeating narration verbatim
- Complex sentences
- More than 3-4 bullet points

### Narration Composition

**Complement, don't repeat:**
- Slides show WHAT, narration explains WHY
- Add context and storytelling
- Reference visuals: "Look at this diagram..."

**Write for speech:**
- Use contractions (don't, it's, we're)
- Spell out numbers under 100
- Short sentences (8-15 words average)
- Natural rhythm with pauses

**Avoid:**
- Reading slides verbatim
- Technical jargon that sounds unnatural spoken
- Long complex sentences
- Abbreviations (say "API" as three letters)

**Example - BAD:**
```
Slide: "62% fixing AI errors"
Narration: "Sixty two percent of developers spend time fixing AI errors."
```

**Example - GOOD:**
```
Slide: "62% fixing AI errors"
Narration: "More than half your time goes to fixing what the AI got wrong.
You're not saving time. You're trading typing for debugging."
```

### Voice Settings

Current voice: `en-GB-RyanNeural` (British, bright, engaging)
Rate: `-8%` (slightly slower for clarity)

---

## Workflow

### 1. Update Slides

Edit `presentation.md` using Marp syntax. Key design principles:
- Use high contrast colors (white text `#ffffff` on dark `#050007`)
- Blue accent: `#4D74FF`
- Orange accent: `#FF5128`
- Keep text readable at 1080p

### 2. Sync Narrations

Update `scripts/slide-narrations.json` to match slides:

```json
[
  {
    "slide": 1,
    "text": "Narration text for slide 1"
  },
  {
    "slide": 2,
    "text": "Narration text for slide 2"
  }
]
```

Ensure:
- One narration entry per slide
- Sequential slide numbers (1, 2, 3...)
- Narration complements (not repeats) slide content

### 3. Clean Up Stale Assets

**Important:** Always clean before regenerating to avoid stale files.

```bash
# Remove old slide images
rm -f assets/slides/slide.*.png

# Remove old video (optional)
rm -f assets/presentation-video.mp4
```

### 4. Generate Slide Images

```bash
# Generate slides
npx @marp-team/marp-cli presentation.md \
  --images png \
  --output assets/slides/slide \
  --allow-local-files

# Add .png extension (marp omits it)
cd assets/slides && for f in slide.[0-9][0-9][0-9]; do mv "$f" "${f}.png"; done && cd ../..
```

### 5. Generate Narrated Video

```bash
python3 scripts/generate-video.py
```

Requires:
- `edge-tts` for text-to-speech
- `ffmpeg` for video encoding

Output: `assets/presentation-video.mp4`

## Keeping in Sync

When updating the presentation:

1. **Add slide** → Add corresponding entry to `slide-narrations.json`
2. **Remove slide** → Remove entry from `slide-narrations.json`
3. **Reorder slides** → Update slide numbers in JSON
4. **Change content** → Update narration to match

### Validation

Before generating video, verify:
- Number of slides matches number of narration entries
- Slide numbers in JSON are sequential (1, 2, 3...)
- No orphaned narrations for non-existent slides

```bash
# Count slides
ls -1 assets/slides/slide.*.png | wc -l

# Count narrations
jq length scripts/slide-narrations.json
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Low contrast text | Update CSS in presentation.md frontmatter |
| Audio too fast/slow | Adjust `RATE` in generate-video.py |
| Video out of sync | Regenerate all slides and audio |
| Code blocks cut off | Reduce font size or split slide |

## Cost Considerations

- **edge-tts**: Free (Microsoft Edge TTS)
- Consider regenerating only changed slides for faster iteration
