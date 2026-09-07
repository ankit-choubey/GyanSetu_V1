"use client";

import { useState, useEffect } from "react";

export function useScrollDirection() {
  const [scrollDirection, setScrollDirection] = useState<"up" | "down">("up");
  const [prevOffset, setPrevOffset] = useState(0);
  const [isAtTop, setIsAtTop] = useState(true);

  useEffect(() => {
    let ticking = false;

    const handleScroll = () => {
      if (!ticking) {
        window.requestAnimationFrame(() => {
          const currentOffset = window.pageYOffset || document.documentElement.scrollTop;
          setIsAtTop(currentOffset < 10);

          if (Math.abs(currentOffset - prevOffset) > 8) {
            if (currentOffset > prevOffset && currentOffset > 64) {
              setScrollDirection("down");
            } else if (currentOffset < prevOffset) {
              setScrollDirection("up");
            }
            setPrevOffset(currentOffset);
          }
          ticking = false;
        });
        ticking = true;
      }
    };

    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, [prevOffset]);

  return { scrollDirection, isAtTop };
}
