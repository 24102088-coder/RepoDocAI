"use client";

import { useEffect, useRef } from "react";

export default function StarfieldBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animationId: number;
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    // ── Stars ────────────────────────────────────
    interface Star {
      x: number;
      y: number;
      radius: number;
      opacity: number;
      twinkleSpeed: number;
      twinklePhase: number;
    }

    const STAR_COUNT = 250;
    const stars: Star[] = Array.from({ length: STAR_COUNT }, () => ({
      x: Math.random() * width,
      y: Math.random() * height,
      radius: Math.random() * 1.8 + 0.3,
      opacity: Math.random(),
      twinkleSpeed: Math.random() * 0.02 + 0.005,
      twinklePhase: Math.random() * Math.PI * 2,
    }));

    // ── Shooting Stars ──────────────────────────
    interface ShootingStar {
      x: number;
      y: number;
      len: number;
      speed: number;
      angle: number;
      opacity: number;
      life: number;
      maxLife: number;
    }

    const shootingStars: ShootingStar[] = [];
    let nextShoot = 120; // frames until next shooting star

    function spawnShootingStar() {
      const angle = Math.random() * 0.5 + 0.3; // 0.3 – 0.8 radians (downward-right)
      shootingStars.push({
        x: Math.random() * width * 0.8,
        y: Math.random() * height * 0.3,
        len: Math.random() * 80 + 40,
        speed: Math.random() * 8 + 6,
        angle,
        opacity: 1,
        life: 0,
        maxLife: Math.random() * 40 + 30,
      });
    }

    // ── Animation loop ──────────────────────────
    let frame = 0;

    function draw() {
      ctx!.clearRect(0, 0, width, height);

      // Draw twinkling stars
      for (const s of stars) {
        s.twinklePhase += s.twinkleSpeed;
        const alpha = 0.3 + 0.7 * ((Math.sin(s.twinklePhase) + 1) / 2);
        ctx!.beginPath();
        ctx!.arc(s.x, s.y, s.radius, 0, Math.PI * 2);
        ctx!.fillStyle = `rgba(255, 255, 255, ${alpha})`;
        ctx!.fill();
      }

      // Spawn shooting stars
      nextShoot--;
      if (nextShoot <= 0) {
        spawnShootingStar();
        nextShoot = Math.floor(Math.random() * 200) + 100; // every 100-300 frames
      }

      // Draw shooting stars
      for (let i = shootingStars.length - 1; i >= 0; i--) {
        const ss = shootingStars[i];
        ss.life++;
        ss.x += Math.cos(ss.angle) * ss.speed;
        ss.y += Math.sin(ss.angle) * ss.speed;
        ss.opacity = 1 - ss.life / ss.maxLife;

        if (ss.opacity <= 0 || ss.x > width + 50 || ss.y > height + 50) {
          shootingStars.splice(i, 1);
          continue;
        }

        const tailX = ss.x - Math.cos(ss.angle) * ss.len;
        const tailY = ss.y - Math.sin(ss.angle) * ss.len;

        const grad = ctx!.createLinearGradient(tailX, tailY, ss.x, ss.y);
        grad.addColorStop(0, `rgba(255, 255, 255, 0)`);
        grad.addColorStop(0.6, `rgba(200, 220, 255, ${ss.opacity * 0.5})`);
        grad.addColorStop(1, `rgba(255, 255, 255, ${ss.opacity})`);

        ctx!.beginPath();
        ctx!.moveTo(tailX, tailY);
        ctx!.lineTo(ss.x, ss.y);
        ctx!.strokeStyle = grad;
        ctx!.lineWidth = 1.5;
        ctx!.stroke();

        // Head glow
        ctx!.beginPath();
        ctx!.arc(ss.x, ss.y, 2, 0, Math.PI * 2);
        ctx!.fillStyle = `rgba(255, 255, 255, ${ss.opacity})`;
        ctx!.fill();
      }

      frame++;
      animationId = requestAnimationFrame(draw);
    }

    draw();

    // Handle resize
    function onResize() {
      width = canvas!.width = window.innerWidth;
      height = canvas!.height = window.innerHeight;
      // Redistribute stars
      for (const s of stars) {
        s.x = Math.random() * width;
        s.y = Math.random() * height;
      }
    }
    window.addEventListener("resize", onResize);

    return () => {
      cancelAnimationFrame(animationId);
      window.removeEventListener("resize", onResize);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 z-0 pointer-events-none"
      style={{ background: "#0a0a1a" }}
    />
  );
}
