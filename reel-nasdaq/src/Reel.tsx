import React from "react";
import { AbsoluteFill, Html5Audio, Img, staticFile, useCurrentFrame } from "remotion";
import { loadFont } from "@remotion/google-fonts/Anton";
import { Character } from "./Character";

const { fontFamily } = loadFont();

export const LOOP = 180; // 6 s a 30 fps
const STRIDE = 45;
const HEADER = "#262930"; // colore della barra "TECHNOLOGY" della heat map
const MAP_TOP = 470;

export type ReelProps = { variant: "originale" | "breve" };

const Outline: React.CSSProperties = {
  WebkitTextStroke: "10px #0b0b10",
  paintOrder: "stroke fill",
  textShadow: "0 8px 0 #0b0b10, 0 0 40px rgba(0,0,0,0.6)",
};
const GTA: React.CSSProperties = {
  color: "#ff5fb0",
  textShadow: "0 8px 0 #0b0b10, 0 0 28px rgba(255,95,176,0.75)",
};

const Caption: React.FC<ReelProps> = ({ variant }) => {
  const base: React.CSSProperties = { fontFamily, color: "#fff", textTransform: "uppercase", lineHeight: 1.02, textAlign: "center" };
  if (variant === "breve") {
    return (
      <div style={base}>
        <div style={{ fontSize: 118, ...Outline }}>
          Il Nasdaq <span style={{ color: "#ff3b3b" }}>crolla.</span>
        </div>
        <div style={{ fontSize: 118, marginTop: 10, ...Outline }}>
          Io: aspetto <span style={GTA}>GTA VI</span>
        </div>
      </div>
    );
  }
  return (
    <div style={base}>
      <div style={{ fontSize: 112, ...Outline }}>
        Il Nasdaq <span style={{ color: "#ff3b3b" }}>crolla</span>
      </div>
      <div style={{ fontSize: 58, marginTop: 14, ...Outline }}>ma tu investi nel lungo periodo</div>
      <div style={{ fontSize: 80, marginTop: 6, ...Outline }}>
        e pensi solo a <span style={GTA}>GTA VI</span>
      </div>
    </div>
  );
};

export const Reel: React.FC<ReelProps> = ({ variant }) => {
  const frame = useCurrentFrame();
  const L = (2 * Math.PI * frame) / LOOP;
  // camera: respiro + deriva + micro "handheld", tutto periodico sul loop
  const scale = 1.06 + 0.04 * Math.sin(L);
  const camX = 14 * Math.sin(L + 1) + 2.5 * Math.sin(5 * L) + 1.5 * Math.sin(9 * L + 2);
  const camY = -10 * Math.cos(L) + 2 * Math.sin(7 * L + 1);
  // personaggio: lieve "dolly" in avanti e indietro
  const charScale = 1 + 0.025 * Math.sin(L - 0.6);

  return (
    <AbsoluteFill style={{ backgroundColor: HEADER, overflow: "hidden" }}>
      <AbsoluteFill
        style={{
          transform: `translate(${camX}px, ${camY}px) scale(${scale})`,
          transformOrigin: "50% 40%",
        }}
      >
        <Img src={staticFile("heatmap.jpg")} style={{ position: "absolute", top: MAP_TOP, left: 0, width: 1080 }} />
      </AbsoluteFill>

      {/* separazione: vignetta scura dietro al personaggio + tramonto in basso */}
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(ellipse 560px 860px at 50% 1400px, rgba(10,6,20,0.55), rgba(10,6,20,0) 70%), linear-gradient(180deg, rgba(0,0,0,0) 72%, rgba(60,10,70,0.55) 88%, rgba(20,4,30,0.85) 100%)",
        }}
      />
      <AbsoluteFill style={{ background: `linear-gradient(180deg, ${HEADER} 0%, ${HEADER} ${MAP_TOP - 40}px, rgba(38,41,48,0) ${MAP_TOP + 30}px)` }} />

      <div style={{ position: "absolute", top: 170, left: 60, right: 60 }}>
        <Caption variant={variant} />
      </div>

      <div
        style={{
          position: "absolute",
          left: 540 - 260,
          top: 729,
          width: 520,
          height: 1170,
          transform: `scale(${charScale})`,
          transformOrigin: "50% 95%",
          filter: "drop-shadow(0 0 26px rgba(255,79,154,0.55)) drop-shadow(0 0 4px rgba(0,0,0,0.8))",
        }}
      >
        <Character frame={frame} loop={LOOP} stride={STRIDE} />
      </div>

      <Html5Audio src={staticFile("music.wav")} />
    </AbsoluteFill>
  );
};
