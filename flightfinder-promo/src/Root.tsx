import { Composition } from "remotion";
import { Promo } from "./Promo";
import "./style.css";

/**
 * FlightFinder Promo Video Composition (30-Second Premium SaaS Style)
 *
 * Specs:
 * - Duration: 30 seconds (900 frames @ 30fps)
 * - Resolution: 1920x1080 (16:9)
 * - Style: Premium SaaS (Stripe/Linear style) with multi-color gradients
 *
 * To preview: npm run dev
 * To render: npm run render
 */

export const RemotionRoot: React.FC = () => {
  return (
    <>
      {/* Main composition - 30 second promo */}
      <Composition
        id="FlightFinderPromo"
        component={Promo}
        durationInFrames={900}
        fps={30}
        width={1920}
        height={1080}
      />

      {/* Individual scene compositions for development/testing */}
      <Composition
        id="HookScene"
        component={require("./scenes/HookScene").HookScene}
        durationInFrames={90}
        fps={30}
        width={1920}
        height={1080}
      />

      <Composition
        id="RevealScene"
        component={require("./scenes/RevealScene").RevealScene}
        durationInFrames={75}
        fps={30}
        width={1920}
        height={1080}
      />

      <Composition
        id="InstallationScene"
        component={require("./scenes/InstallationScene").InstallationScene}
        durationInFrames={165}
        fps={30}
        width={1920}
        height={1080}
      />

      <Composition
        id="DemoScene"
        component={require("./scenes/DemoScene").DemoScene}
        durationInFrames={375}
        fps={30}
        width={1920}
        height={1080}
      />

      <Composition
        id="CTAScene"
        component={require("./scenes/CTAScene").CTAScene}
        durationInFrames={255}
        fps={30}
        width={1920}
        height={1080}
      />

    </>
  );
};
