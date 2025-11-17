-- Seed data for development
-- This file is run after all migrations during `supabase db reset`

-- Insert some test data for development (only if not in production)
INSERT INTO early_access_signups (email, first_name, last_name, feature_interest, comment)
VALUES
  ('test1@example.com', 'John', 'Doe', 'Dashboard', 'Excited about the dashboard feature!'),
  ('test2@example.com', 'Jane', 'Smith', 'Goals', 'Looking forward to setting fitness goals'),
  ('test3@example.com', 'Mike', 'Johnson', 'Advanced Intervals', 'Need more advanced workout customization')
ON CONFLICT (email) DO NOTHING; -- Évite les erreurs si déjà inséré
