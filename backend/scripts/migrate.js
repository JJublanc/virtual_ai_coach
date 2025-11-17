#!/usr/bin/env node
/**
 * Script de migration pour Supabase
 * Usage: node scripts/migrate.js [environment]
 */

const { exec } = require('child_process');
const path = require('path');

// Load environment variables
require('dotenv').config({ path: path.join(__dirname, '..', '.env') });

const environment = process.argv[2] || 'local';

console.log(`🚀 Running migrations for environment: ${environment}`);

let command;
const cwd = path.join(__dirname, '..');

switch (environment) {
  case 'local':
  case 'dev':
    // Migration vers projet dev cloud (utilise --linked au lieu de --project-ref)
    const devId = process.env.SUPABASE_DEV_PROJECT_ID;
    if (!devId) {
      console.error('❌ SUPABASE_DEV_PROJECT_ID not set in .env');
      console.log('📝 Add this to backend/.env:');
      console.log('   SUPABASE_DEV_PROJECT_ID=your-dev-ref-id');
      console.log('\n⚠️  Also run: supabase link --project-ref your-dev-ref-id');
      process.exit(1);
    }
    // Utilise --linked qui lit la configuration du projet lié
    command = `supabase db push --linked`;
    break;

  case 'staging':
    // Migration vers staging
    const stagingId = process.env.SUPABASE_STAGING_PROJECT_ID;
    if (!stagingId) {
      console.error('❌ SUPABASE_STAGING_PROJECT_ID not set in .env');
      console.log('📝 Add this to backend/.env:');
      console.log('   SUPABASE_STAGING_PROJECT_ID=your-staging-ref-id');
      process.exit(1);
    }
    command = `supabase db push --db-url postgresql://postgres:${process.env.SUPABASE_STAGING_DB_PASSWORD || '[password]'}@db.${stagingId}.supabase.co:5432/postgres`;
    break;

  case 'production':
    // Migration vers production
    const prodId = process.env.SUPABASE_PROD_PROJECT_ID;
    if (!prodId) {
      console.error('❌ SUPABASE_PROD_PROJECT_ID not set in .env');
      console.log('📝 Add this to backend/.env:');
      console.log('   SUPABASE_PROD_PROJECT_ID=your-prod-ref-id');
      process.exit(1);
    }
    console.log('⚠️  Production migration - please confirm');
    command = `supabase db push --db-url postgresql://postgres:${process.env.SUPABASE_PROD_DB_PASSWORD || '[password]'}@db.${prodId}.supabase.co:5432/postgres`;
    break;

  default:
    console.error('❌ Unknown environment. Use: dev (or local), staging, or production');
    process.exit(1);
}

exec(command, { cwd, env: process.env }, (error, stdout, stderr) => {
  if (error) {
    console.error(`❌ Migration failed: ${error.message}`);
    console.log('\n💡 Troubleshooting:');
    console.log('   1. Make sure Supabase CLI is installed: supabase --version');
    console.log('   2. For dev/local: Run "supabase link --project-ref your-dev-id" first');
    console.log('   3. For staging/prod: Add DB_PASSWORD to your .env file');
    console.log('   4. Check your .env file has the correct PROJECT_ID');
    process.exit(1);
  }

  if (stderr) {
    console.warn(`⚠️  ${stderr}`);
  }

  console.log(`✅ Migration completed:\n${stdout}`);
});
