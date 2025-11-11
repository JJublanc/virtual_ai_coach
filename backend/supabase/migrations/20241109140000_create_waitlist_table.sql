-- Migration: Create waitlist table for authenticated users
-- This replaces the early_access_signups table approach with proper auth integration

-- Create waitlist table linked to auth.users
CREATE TABLE IF NOT EXISTS public.waitlist (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  feature_name text NOT NULL,
  comment text,
  created_at timestamptz DEFAULT now() NOT NULL,
  updated_at timestamptz DEFAULT now() NOT NULL,

  -- Ensure a user can only be on the waitlist once per feature
  UNIQUE(user_id, feature_name)
);

-- Create index for faster lookups
CREATE INDEX idx_waitlist_user_id ON public.waitlist(user_id);
CREATE INDEX idx_waitlist_feature_name ON public.waitlist(feature_name);
CREATE INDEX idx_waitlist_created_at ON public.waitlist(created_at DESC);

-- Add comment for documentation
COMMENT ON TABLE public.waitlist IS 'Stores users interested in upcoming features';
COMMENT ON COLUMN public.waitlist.user_id IS 'Reference to authenticated user';
COMMENT ON COLUMN public.waitlist.feature_name IS 'Name of the feature (e.g., "dashboard", "profile", etc.)';
COMMENT ON COLUMN public.waitlist.comment IS 'Optional user comment or suggestion about the feature';
