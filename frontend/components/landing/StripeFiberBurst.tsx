"use client";

import React, { useEffect, useRef } from "react";

interface Filament {
  baseAngle: number; // horizontal angle in radians (-PI * 0.44 to +PI * 0.44)
  depthAngle: number; // 3D z-depth angle
  baseLength: number; // resting length
  curviness: number; // resting curvature

  // Spring physics variables for interactive deflection
  tipDispX: number;
  tipDispY: number;
  tipDispZ: number;
  vx: number;
  vy: number;
  vz: number;

  // Visual attributes
  thickness: number;
  tipSpark: boolean;
  pulsePhase: number;
  pulseSpeed: number;
  proximityEnergy: number; // 0 to 1 glow excitement near cursor
}

export function StripeFiberBurst() {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;

    const ctx = canvas.getContext("2d", { alpha: true });
    if (!ctx) return;

    let animationFrameId: number;
    let width = container.clientWidth;
    let height = container.clientHeight;

    const dpr = Math.min(window.devicePixelRatio || 1, 2);

    const handleResize = () => {
      if (!container || !canvas) return;
      width = container.clientWidth;
      height = container.clientHeight;
      canvas.width = width * dpr;
      canvas.height = height * dpr;
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;
      ctx.scale(dpr, dpr);
    };

    handleResize();
    window.addEventListener("resize", handleResize);

    // =========================================================================
    // INITIALIZE 400 CONTINUOUS 3D FIBER-OPTIC FILAMENTS (OPTIMIZED)
    // =========================================================================
    const FILAMENT_COUNT = 900;
    const filaments: Filament[] = [];

    for (let i = 0; i < FILAMENT_COUNT; i++) {
      const u = (i + Math.random() * 0.7) / FILAMENT_COUNT; // strictly monotonic 0 to 1
      const normalizedAngle = (u - 0.5) * 2; // -1 to +1

      // Wide radial fan: spans full width like Stripe (~160 degrees)
      const baseAngle = normalizedAngle * (Math.PI * 0.82);

      // Depth angle: spherical dome distribution
      const depthAngle = (Math.random() - 0.5) * 1.8;

      // Filament length: short and contained in bottom portion like Stripe
      const domeProfile = Math.cos(normalizedAngle * (Math.PI * 0.45));
      const baseLength =
        height * 0.22 + domeProfile * (height * 0.18) + (Math.random() - 0.5) * (height * 0.50);

      // Gentle natural outward bend
      const curviness = Math.sin(baseAngle) * (0.08 + Math.random() * 0.07);

      filaments.push({
        baseAngle,
        depthAngle,
        baseLength: Math.max(100, baseLength),
        curviness,
        tipDispX: 0,
        tipDispY: 0,
        tipDispZ: 0,
        vx: 0,
        vy: 0,
        vz: 0,
        thickness: 0.55 + Math.random() * 0.75,
        tipSpark: Math.random() > 0.3,
        pulsePhase: Math.random() * Math.PI * 2,
        pulseSpeed: 0.02 + Math.random() * 0.03,
        proximityEnergy: 0,
      });
    }

    // =========================================================================
    // MOUSE STATE & VELOCITY TRACKING
    // =========================================================================
    const mouse = {
      x: -9999,
      y: -9999,
      normX: 0,
      normY: 0,
      vx: 0,
      vy: 0,
      lastX: -9999,
      lastY: -9999,
      active: false,
    };

    const handleMouseMove = (e: MouseEvent) => {
      const rect = container.getBoundingClientRect();
      const clientX = e.clientX - rect.left;
      const clientY = e.clientY - rect.top;

      if (mouse.lastX !== -9999) {
        mouse.vx = clientX - mouse.lastX;
        mouse.vy = clientY - mouse.lastY;
      }
      mouse.lastX = clientX;
      mouse.lastY = clientY;
      mouse.x = clientX;
      mouse.y = clientY;
      mouse.normX = (clientX / width - 0.5) * 2;
      mouse.normY = (clientY / height - 0.5) * 2;
      mouse.active = true;
    };

    const handleMouseLeave = () => {
      mouse.active = false;
      mouse.normX = 0;
      mouse.normY = 0;
      mouse.x = -9999;
      mouse.y = -9999;
      mouse.vx = 0;
      mouse.vy = 0;
    };

    container.addEventListener("mousemove", handleMouseMove);
    container.addEventListener("mouseleave", handleMouseLeave);

    // =========================================================================
    // COMPACT PHYSICS & RENDERING LOOP
    // =========================================================================
    let time = 0;
    let smoothCamYaw = 0;
    let smoothCamPitch = 0;

    const FOCAL_LENGTH = 550;
    const INFLUENCE_RADIUS = 150; // Tightly calibrated to compact size
    const SPRING_K = 0.075; // Snappy elastic response
    const DAMPING = 0.82; // Natural damping

    const render = () => {
      time += 0.016;

      // Smooth camera yaw & pitch
      const targetCamYaw = mouse.active ? mouse.normX * 0.16 : Math.sin(time * 0.4) * 0.025;
      const targetCamPitch = mouse.active ? -mouse.normY * 0.1 : Math.cos(time * 0.3) * 0.015;
      smoothCamYaw += (targetCamYaw - smoothCamYaw) * 0.09;
      smoothCamPitch += (targetCamPitch - smoothCamPitch) * 0.09;

      const cosYaw = Math.cos(smoothCamYaw);
      const sinYaw = Math.sin(smoothCamYaw);
      const cosPitch = Math.cos(smoothCamPitch);
      const sinPitch = Math.sin(smoothCamPitch);

      ctx.clearRect(0, 0, width, height);

      const originX = width / 2;
      const originY = height + 8; // submerged for clean horizon

      mouse.vx *= 0.85;
      mouse.vy *= 0.85;

      interface RenderableFilament {
        p0: { x: number; y: number };
        p1: { x: number; y: number };
        p2: { x: number; y: number };
        z: number;
        thickness: number;
        tipSpark: boolean;
        proximityEnergy: number;
        alpha: number;
      }

      const renderables: RenderableFilament[] = [];

      for (let i = 0; i < FILAMENT_COUNT; i++) {
        const fil = filaments[i];

        const angle = fil.baseAngle;
        const len = fil.baseLength;
        const phi = fil.depthAngle;

        const restTipX = Math.sin(angle) * Math.cos(phi) * len;
        const restTipY = -Math.cos(angle) * Math.cos(phi) * len;
        const restTipZ = Math.sin(phi) * len;

        const currentTipX = restTipX + fil.tipDispX;
        const currentTipY = restTipY + fil.tipDispY;
        const currentTipZ = restTipZ + fil.tipDispZ;

        const x1 = currentTipX * cosYaw + currentTipZ * sinYaw;
        const z1 = -currentTipX * sinYaw + currentTipZ * cosYaw;
        const y2 = currentTipY * cosPitch - z1 * sinPitch;
        const z2 = currentTipY * sinPitch + z1 * cosPitch;

        const scale = FOCAL_LENGTH / (FOCAL_LENGTH + z2);
        const screenTipX = originX + x1 * scale;
        const screenTipY = originY + y2 * scale;

        let externalForceX = 0;
        let externalForceY = 0;
        let externalForceZ = 0;

        if (mouse.active) {
          const dx = screenTipX - mouse.x;
          const dy = screenTipY - mouse.y;
          const dist = Math.sqrt(dx * dx + dy * dy);

          if (dist < INFLUENCE_RADIUS) {
            const factor = Math.pow(1 - dist / INFLUENCE_RADIUS, 2);
            fil.proximityEnergy += (factor - fil.proximityEnergy) * 0.25;

            const pushMagnitude = factor * 3.8;
            const pushDirX = dist > 1 ? dx / dist : 0;
            const pushDirY = dist > 1 ? dy / dist : 0;

            externalForceX = pushDirX * pushMagnitude + mouse.vx * factor * 0.3;
            externalForceY = pushDirY * pushMagnitude + mouse.vy * factor * 0.3;
            externalForceZ = -factor * 2.5;
          } else {
            fil.proximityEnergy *= 0.94;
          }
        } else {
          fil.proximityEnergy *= 0.94;
        }

        const springFx = -SPRING_K * fil.tipDispX;
        const springFy = -SPRING_K * fil.tipDispY;
        const springFz = -SPRING_K * fil.tipDispZ;

        fil.vx = (fil.vx + springFx + externalForceX) * DAMPING;
        fil.vy = (fil.vy + springFy + externalForceY) * DAMPING;
        fil.vz = (fil.vz + springFz + externalForceZ) * DAMPING;

        fil.tipDispX += fil.vx;
        fil.tipDispY += fil.vy;
        fil.tipDispZ += fil.vz;

        const restMidX = Math.sin(angle + fil.curviness) * Math.cos(phi) * (len * 0.5);
        const restMidY = -Math.cos(angle + fil.curviness) * Math.cos(phi) * (len * 0.5);
        const restMidZ = Math.sin(phi) * (len * 0.5);

        const currentMidX = restMidX + fil.tipDispX * 0.45;
        const currentMidY = restMidY + fil.tipDispY * 0.45;
        const currentMidZ = restMidZ + fil.tipDispZ * 0.45;

        const mx1 = currentMidX * cosYaw + currentMidZ * sinYaw;
        const mz1 = -currentMidX * sinYaw + currentMidZ * cosYaw;
        const my2 = currentMidY * cosPitch - mz1 * sinPitch;
        const mz2 = currentMidY * sinPitch + mz1 * cosPitch;

        const midScale = FOCAL_LENGTH / (FOCAL_LENGTH + mz2);
        const screenMidX = originX + mx1 * midScale;
        const screenMidY = originY + my2 * midScale;

        renderables.push({
          p0: { x: originX, y: originY },
          p1: { x: screenMidX, y: screenMidY },
          p2: { x: screenTipX, y: screenTipY },
          z: z2,
          thickness: fil.thickness * Math.max(0.5, Math.min(1.3, scale)),
          tipSpark: fil.tipSpark,
          proximityEnergy: fil.proximityEnergy,
          alpha: Math.max(0.2, Math.min(1.0, scale * 0.9)),
        });
      }

      renderables.sort((a, b) => b.z - a.z);

      ctx.lineCap = "round";

      for (let i = 0; i < renderables.length; i++) {
        const item = renderables[i];
        const { p0, p1, p2, thickness, tipSpark, proximityEnergy, alpha } = item;

        const grad = ctx.createLinearGradient(p0.x, p0.y, p2.x, p2.y);
        grad.addColorStop(0, "rgba(255, 255, 255, 0.98)");
        grad.addColorStop(0.3, "rgba(255, 255, 255, 0.85)");
        const tipWhite = Math.min(1, 0.6 + proximityEnergy * 0.4);
        const tipOpacity = Math.min(1, alpha * (0.55 + proximityEnergy * 0.45));
        grad.addColorStop(0.7, `rgba(224, 231, 255, ${tipOpacity * 0.8})`);
        grad.addColorStop(1, `rgba(255, 255, 255, ${tipOpacity * tipWhite})`);

        ctx.beginPath();
        ctx.moveTo(p0.x, p0.y);
        ctx.quadraticCurveTo(p1.x, p1.y, p2.x, p2.y);

        ctx.lineWidth = thickness * (1 + proximityEnergy * 0.4);
        ctx.strokeStyle = grad;
        ctx.stroke();

        if (tipSpark && p2.y > 0 && p2.y < height) {
          const sparkRadius = (0.6 + proximityEnergy * 0.8) * (thickness / 0.75);
          ctx.beginPath();
          ctx.arc(p2.x, p2.y, sparkRadius, 0, Math.PI * 2);
          ctx.fillStyle = `rgba(255, 255, 255, ${0.7 + proximityEnergy * 0.3})`;
          ctx.fill();
        }
      }

      // Luminous Horizon Bloom (Slightly reduced intensity)
      const horizonRadius = Math.max(9, width * 0.48);
      const ambientGlow = ctx.createRadialGradient(
        originX,
        originY,
        8,
        originX,
        originY,
        horizonRadius
      );
      ambientGlow.addColorStop(0, "rgba(59, 130, 246, 0.35)");
      ambientGlow.addColorStop(0.25, "rgba(37, 99, 235, 0.15)");
      ambientGlow.addColorStop(0.6, "rgba(23, 23, 66, 0.05)");
      ambientGlow.addColorStop(1, "rgba(11, 14, 46, 0)");

      ctx.fillStyle = ambientGlow;
      ctx.beginPath();
      ctx.arc(originX, originY, horizonRadius, Math.PI, 0);
      ctx.fill();

      const coreRadius = Math.max(1, width * 0.18);
      const coreBloom = ctx.createRadialGradient(
        originX,
        originY,
        0,
        originX,
        originY,
        coreRadius
      );
      coreBloom.addColorStop(0, "rgba(255, 255, 255, 0.85)");
      coreBloom.addColorStop(0.12, "rgba(224, 238, 255, 0.70)");
      coreBloom.addColorStop(0.35, "rgba(96, 165, 250, 0.35)");
      coreBloom.addColorStop(0.7, "rgba(37, 99, 235, 0.08)");
      coreBloom.addColorStop(1, "rgba(11, 14, 46, 0)");

      ctx.fillStyle = coreBloom;
      ctx.beginPath();
      ctx.arc(originX, originY, coreRadius, Math.PI, 0);
      ctx.fill();

      const horizonLine = ctx.createLinearGradient(
        originX - width * 0.35,
        originY,
        originX + width * 0.35,
        originY
      );
      horizonLine.addColorStop(0, "rgba(255, 255, 255, 0)");
      horizonLine.addColorStop(0.3, "rgba(191, 219, 254, 0.7)");
      horizonLine.addColorStop(0.5, "rgba(255, 255, 255, 1)");
      horizonLine.addColorStop(0.7, "rgba(191, 219, 254, 0.7)");
      horizonLine.addColorStop(1, "rgba(255, 255, 255, 0)");

      ctx.beginPath();
      ctx.moveTo(originX - width * 0.35, originY - 1);
      ctx.lineTo(originX + width * 0.35, originY - 1);
      ctx.strokeStyle = horizonLine;
      ctx.lineWidth = 2;
      ctx.stroke();

      animationFrameId = requestAnimationFrame(render);
    };

    animationFrameId = requestAnimationFrame(render);

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener("resize", handleResize);
      container.removeEventListener("mousemove", handleMouseMove);
      container.removeEventListener("mouseleave", handleMouseLeave);
    };
  }, []);

  return (
    <div
      ref={containerRef}
      className="relative w-full h-full min-h-[340px] overflow-hidden cursor-default select-none"
    >
      <canvas
        ref={canvasRef}
        className="absolute inset-0 block w-full h-full pointer-events-none"
      />
    </div>
  );
}
