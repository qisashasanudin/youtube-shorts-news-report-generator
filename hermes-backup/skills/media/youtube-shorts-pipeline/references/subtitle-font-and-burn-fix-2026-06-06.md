## Subtitle font / burn fix (2026-06-06)

Subtitle styling changed from Burbank Big Condensed to Whoosh at size 90, because Burbank was not applying reliably from the provided OTF and the user explicitly prefers Whoosh.

Verified source asset:
- `assets/fonts/whoosh/burbank_big_condensed.otf`

Working ASS style line:
- `Style: Default,Whoosh,90,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,1,0,1,3,0.3,2,60,60,120,1`

Working ffmpeg burn:
- `subtitles=captions/captions.ass:fontsdir=assets/fonts/whoosh:force_style='FontName=Whoosh,FontSize=90,...'`

Key rules:
- Prefer ASS font control from the base `Style:` line, not inline overrides.
- Keep cue text uppercase and one-word per subtitle when using this channel style.
- If Whoosh fails to render, verify the OTF family name matches `Fontname`, check the absolute path from the render working directory, and do a frame check at an active cue timestamp.

Reverted from prior Burbank attempt:
- Burbank Big Condensed had been used in ASS base and force_style at 64pt/72pt before Whoosh.
- Burbank was replaced specifically because it was not reliably applied.
