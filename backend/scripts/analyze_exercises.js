/**
 * Script pour analyser et afficher des statistiques sur les exercices
 *
 * Usage:
 *   node backend/scripts/analyze_exercises.js
 *
 * Affiche:
 *   - Nombre total d'exercices
 *   - Répartition par difficulté (easy, medium, hard)
 *   - Répartition par type (avec/sans saut)
 *   - Répartition par latéralité
 *   - Statistiques sur la durée et les calories
 */

const fs = require('fs');
const path = require('path');

// Chemin du fichier exercises.json
const EXERCISES_JSON_PATH = path.join(__dirname, 'exercises.json');

/**
 * Charge les exercices depuis exercises.json
 */
function loadExercises() {
  if (!fs.existsSync(EXERCISES_JSON_PATH)) {
    console.error(`❌ Erreur: Fichier ${EXERCISES_JSON_PATH} introuvable`);
    process.exit(1);
  }

  const content = fs.readFileSync(EXERCISES_JSON_PATH, 'utf-8');
  return JSON.parse(content);
}

/**
 * Calcule les statistiques sur les exercices
 */
function analyzeExercises(exercises) {
  const stats = {
    total: exercises.length,
    byDifficulty: {},
    byJump: { with_jump: 0, without_jump: 0 },
    byLaterality: {},
    byAccessTier: {},
    avgDuration: 0,
    avgCalories: 0,
    musclesTargeted: new Set(),
  };

  let totalDuration = 0;
  let totalCalories = 0;

  exercises.forEach(exercise => {
    // Difficulté
    const difficulty = exercise.difficulty || 'unknown';
    stats.byDifficulty[difficulty] = (stats.byDifficulty[difficulty] || 0) + 1;

    // Jump
    if (exercise.has_jump) {
      stats.byJump.with_jump++;
    } else {
      stats.byJump.without_jump++;
    }

    // Latéralité
    const laterality = exercise.metadata?.laterality || 'unknown';
    stats.byLaterality[laterality] = (stats.byLaterality[laterality] || 0) + 1;

    // Access tier
    const tier = exercise.access_tier || 'unknown';
    stats.byAccessTier[tier] = (stats.byAccessTier[tier] || 0) + 1;

    // Durée et calories
    totalDuration += exercise.default_duration || 0;
    totalCalories += exercise.metadata?.calories_per_min || 0;

    // Muscles ciblés
    if (exercise.metadata?.muscles_targeted) {
      exercise.metadata.muscles_targeted.forEach(muscle => {
        stats.musclesTargeted.add(muscle);
      });
    }
  });

  stats.avgDuration = totalDuration / exercises.length;
  stats.avgCalories = totalCalories / exercises.length;

  return stats;
}

/**
 * Affiche les statistiques de manière formatée
 */
function displayStats(stats, exercises) {
  console.log('\n╔══════════════════════════════════════════════════════════╗');
  console.log('║         📊 STATISTIQUES DES EXERCICES                   ║');
  console.log('╚══════════════════════════════════════════════════════════╝\n');

  // Total
  console.log(`📋 TOTAL: ${stats.total} exercices\n`);

  // Par difficulté
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('🎯 RÉPARTITION PAR DIFFICULTÉ:');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  Object.entries(stats.byDifficulty).sort().forEach(([difficulty, count]) => {
    const percentage = ((count / stats.total) * 100).toFixed(1);
    const icon = difficulty === 'easy' ? '🟢' : difficulty === 'medium' ? '🟡' : difficulty === 'hard' ? '🔴' : '⚪';
    const bar = '█'.repeat(Math.round(count / 2));
    console.log(`   ${icon} ${difficulty.padEnd(10)}: ${count.toString().padStart(3)} (${percentage}%) ${bar}`);
  });

  // Par type (jump/no jump)
  console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('🦘 RÉPARTITION PAR TYPE:');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  const jumpPercentage = ((stats.byJump.with_jump / stats.total) * 100).toFixed(1);
  const noJumpPercentage = ((stats.byJump.without_jump / stats.total) * 100).toFixed(1);
  console.log(`   🚀 Avec sauts    : ${stats.byJump.with_jump.toString().padStart(3)} (${jumpPercentage}%)`);
  console.log(`   🧘 Sans sauts    : ${stats.byJump.without_jump.toString().padStart(3)} (${noJumpPercentage}%)`);

  // Par latéralité
  console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('↔️  RÉPARTITION PAR LATÉRALITÉ:');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  Object.entries(stats.byLaterality).sort().forEach(([laterality, count]) => {
    const percentage = ((count / stats.total) * 100).toFixed(1);
    const icon = laterality === 'bilateral' ? '↔️' : laterality === 'left' ? '⬅️' : laterality === 'right' ? '➡️' : '❓';
    console.log(`   ${icon} ${laterality.padEnd(12)}: ${count.toString().padStart(3)} (${percentage}%)`);
  });

  // Par access tier
  console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('🔓 RÉPARTITION PAR ACCESS TIER:');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  Object.entries(stats.byAccessTier).sort().forEach(([tier, count]) => {
    const percentage = ((count / stats.total) * 100).toFixed(1);
    console.log(`   🎫 ${tier.padEnd(12)}: ${count.toString().padStart(3)} (${percentage}%)`);
  });

  // Moyennes
  console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('📈 MOYENNES:');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log(`   ⏱️  Durée moyenne      : ${stats.avgDuration.toFixed(0)} secondes`);
  console.log(`   🔥 Calories moyennes  : ${stats.avgCalories.toFixed(1)} cal/min`);

  // Muscles ciblés
  console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('💪 GROUPES MUSCULAIRES CIBLÉS:');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  const muscles = Array.from(stats.musclesTargeted).sort();
  console.log(`   ${muscles.length} groupes musculaires différents:`);
  const muscleRows = [];
  for (let i = 0; i < muscles.length; i += 3) {
    muscleRows.push(muscles.slice(i, i + 3));
  }
  muscleRows.forEach(row => {
    console.log(`   • ${row.map(m => m.padEnd(20)).join(' ')}`);
  });

  // Exercices symétriques
  console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('🔄 EXERCICES SYMÉTRIQUES:');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  const symmetricExercises = exercises.filter(e => e.metadata?.symmetric_exercise_id);
  console.log(`   ${symmetricExercises.length} exercices avec symétrie (${(symmetricExercises.length / stats.total * 100).toFixed(1)}%)`);

  // Paires symétriques
  const pairs = new Set();
  symmetricExercises.forEach(ex => {
    const pairId = [ex.id, ex.metadata.symmetric_exercise_id].sort().join('-');
    pairs.add(pairId);
  });
  console.log(`   ${pairs.size} paires symétriques`);

  console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
}

/**
 * Fonction principale
 */
function main() {
  console.log('\n🔍 Analyse des exercices en cours...\n');

  const exercises = loadExercises();
  const stats = analyzeExercises(exercises);
  displayStats(stats, exercises);
}

// Exécuter
main();
