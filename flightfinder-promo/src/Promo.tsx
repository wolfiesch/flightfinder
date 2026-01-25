import React from "react";
import { TransitionSeries, linearTiming } from "@remotion/transitions";
import { fade } from "@remotion/transitions/fade";
import { slide } from "@remotion/transitions/slide";

import {
  HookScene,
  RevealScene,
  InstallationScene,
  DemoScene,
  CTAScene,
} from "./scenes";

/**
 * FlightFinder 30-Second Promo Video (Premium SaaS Style)
 *
 * Total duration: 900 frames (30s @ 30fps)
 *
 * Scene breakdown with transitions:
 * - 4 transitions × 15 frames = 60 frames overlap
 *
 * Scene timing:
 * 1. Hook:        0-3s    (90 frames)  - "Tired of API key hell?"
 * 2. Reveal:      2.5-5s  (75 frames)  - Logo + "Zero API Keys" badge
 * 3. Install:     4.5-10s (165 frames) - Fast typewriter install
 * 4. Demo:        9.5-22s (375 frames) - Combined flight/hotel/trip
 * 5. CTA:         21.5-30s (255 frames) - "One command. No API key."
 *
 * Sum: 90+75+165+375+255 = 960
 * Minus 4 transitions × 15 = 60
 * Total: 960 - 60 = 900 frames ✓
 */

const TRANSITION_DURATION = 15;

const fadeTransition = {
  presentation: fade(),
  timing: linearTiming({ durationInFrames: TRANSITION_DURATION }),
};

const slideFromRightTransition = {
  presentation: slide({ direction: "from-right" }),
  timing: linearTiming({ durationInFrames: TRANSITION_DURATION }),
};

export const Promo: React.FC = () => {
  return (
    <TransitionSeries>
      {/* Scene 1: Hook - Provocative question (0-3s) */}
      <TransitionSeries.Sequence durationInFrames={90}>
        <HookScene />
      </TransitionSeries.Sequence>

      <TransitionSeries.Transition {...fadeTransition} />

      {/* Scene 2: Reveal - Logo and badge (2.5-5s) */}
      <TransitionSeries.Sequence durationInFrames={75}>
        <RevealScene />
      </TransitionSeries.Sequence>

      <TransitionSeries.Transition {...slideFromRightTransition} />

      {/* Scene 3: Installation - Fast typewriter (4.5-10s) */}
      <TransitionSeries.Sequence durationInFrames={165}>
        <InstallationScene />
      </TransitionSeries.Sequence>

      <TransitionSeries.Transition {...fadeTransition} />

      {/* Scene 4: Demo - Combined flight/hotel/trip (9.5-22s) */}
      <TransitionSeries.Sequence durationInFrames={375}>
        <DemoScene />
      </TransitionSeries.Sequence>

      <TransitionSeries.Transition {...fadeTransition} />

      {/* Scene 5: CTA - Final call to action (21.5-30s) */}
      <TransitionSeries.Sequence durationInFrames={255}>
        <CTAScene />
      </TransitionSeries.Sequence>
    </TransitionSeries>
  );
};
