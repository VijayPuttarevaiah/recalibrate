import { useCallback, useEffect, useRef, useState } from "react";

/**
 * Manages resend cooldown for OTP/code flows.
 * start_timer() starts a countdown from initial_seconds to 0.
 */
export function use_resend_timer(initial_seconds = 60) {
  const [time_left, setTimeLeft] = useState(0);
  const interval_ref = useRef(null);

  const clear_timer = useCallback(() => {
    if (interval_ref.current) {
      clearInterval(interval_ref.current);
      interval_ref.current = null;
    }
  }, []);

  const start_timer = useCallback(() => {
    clear_timer();
    setTimeLeft(initial_seconds);

    interval_ref.current = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 1) {
          clear_timer();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  }, [clear_timer, initial_seconds]);

  useEffect(() => {
    return () => clear_timer();
  }, [clear_timer]);

  const is_blocked = time_left > 0;

  return { time_left, is_blocked, start_timer };
}
