import { Composition } from "remotion";
import { LOOP, Reel } from "./Reel";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition id="ReelOriginale" component={Reel} durationInFrames={LOOP} fps={30} width={1080} height={1920} defaultProps={{ variant: "originale" as const }} />
      <Composition id="ReelBreve" component={Reel} durationInFrames={LOOP} fps={30} width={1080} height={1920} defaultProps={{ variant: "breve" as const }} />
    </>
  );
};
