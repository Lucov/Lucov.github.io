#!/usr/bin/env node
/**
 * Test script to verify health stats functionality
 * Run with: node test-health-stats.js
 */

const fs = require('fs');
const path = require('path');

// Colors for terminal output
const colors = {
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  reset: '\x1b[0m'
};

function log(status, message) {
  const icons = {
    pass: `${colors.green}✓${colors.reset}`,
    fail: `${colors.red}✗${colors.reset}`,
    info: `${colors.blue}ℹ${colors.reset}`,
    warn: `${colors.yellow}⚠${colors.reset}`
  };
  console.log(`${icons[status]} ${message}`);
}

// Test data freshness check
function checkDataFreshness(data, maxAgeHours = 48) {
  if (!data.lastUpdated) {
    return { isFresh: false, message: 'No timestamp found' };
  }

  const lastUpdate = new Date(data.lastUpdated);
  if (isNaN(lastUpdate.getTime())) {
    return { isFresh: false, message: `Invalid timestamp: ${data.lastUpdated}` };
  }

  const nowUtc = Date.now();
  const lastUpdateUtc = lastUpdate.getTime();
  const hoursSinceUpdate = (nowUtc - lastUpdateUtc) / (1000 * 60 * 60);

  return {
    isFresh: hoursSinceUpdate <= maxAgeHours,
    hoursSinceUpdate: Math.round(hoursSinceUpdate * 10) / 10,
    message: `Data is ${hoursSinceUpdate.toFixed(1)} hours old (max: ${maxAgeHours})`
  };
}

// Test data validation
function validateData(data) {
  const dailyStats = data.dailyStats || {};
  const availableData = [];

  if (dailyStats.sleep?.score != null) availableData.push('sleep');
  if (dailyStats.heartRate?.resting != null) availableData.push('heartRate');
  if (dailyStats.activity?.steps != null) availableData.push('activity');
  if (dailyStats.energy?.score != null) availableData.push('energy');
  if (dailyStats.stress?.average != null) availableData.push('stress');

  return {
    isValid: availableData.length > 0,
    availableData,
    message: availableData.length > 0
      ? `Found ${availableData.length} data types: ${availableData.join(', ')}`
      : 'No valid data found'
  };
}

// Main test runner
async function runTests() {
  console.log('\n' + '='.repeat(50));
  console.log('Health Stats Test Suite');
  console.log('='.repeat(50) + '\n');

  let passed = 0;
  let failed = 0;

  // Test 1: Load health data file
  console.log('Test 1: Loading health-data.json');
  let healthData;
  try {
    const dataPath = path.join(__dirname, 'health-data.json');
    const rawData = fs.readFileSync(dataPath, 'utf8');
    healthData = JSON.parse(rawData);
    log('pass', 'Health data file loaded successfully');
    passed++;
  } catch (error) {
    log('fail', `Failed to load health data: ${error.message}`);
    failed++;
    return;
  }

  // Test 2: Validate timestamp format
  console.log('\nTest 2: Timestamp validation');
  if (healthData.lastUpdated) {
    const date = new Date(healthData.lastUpdated);
    if (!isNaN(date.getTime())) {
      log('pass', `Valid timestamp: ${healthData.lastUpdated}`);
      log('info', `Parsed as: ${date.toISOString()}`);
      passed++;
    } else {
      log('fail', `Invalid timestamp format: ${healthData.lastUpdated}`);
      failed++;
    }
  } else {
    log('fail', 'Missing lastUpdated field');
    failed++;
  }

  // Test 3: Data freshness check
  console.log('\nTest 3: Data freshness check (48 hour limit)');
  const freshnessResult = checkDataFreshness(healthData, 48);
  if (freshnessResult.isFresh) {
    log('pass', freshnessResult.message);
    passed++;
  } else {
    log('warn', freshnessResult.message);
    log('info', 'Card would show "Data is outdated" message');
    failed++;
  }

  // Test 4: Data validation
  console.log('\nTest 4: Data field validation');
  const validationResult = validateData(healthData);
  if (validationResult.isValid) {
    log('pass', validationResult.message);
    passed++;
  } else {
    log('fail', validationResult.message);
    failed++;
  }

  // Test 5: Check individual data fields
  console.log('\nTest 5: Individual field checks');
  const dailyStats = healthData.dailyStats || {};

  const fields = [
    { name: 'Sleep score', value: dailyStats.sleep?.score, expected: 'number' },
    { name: 'Sleep duration', value: dailyStats.sleep?.duration, expected: 'number' },
    { name: 'Energy score', value: dailyStats.energy?.score, expected: 'number' },
    { name: 'Resting HR', value: dailyStats.heartRate?.resting, expected: 'number' },
    { name: 'Steps', value: dailyStats.activity?.steps, expected: 'number' },
    { name: 'Stress level', value: dailyStats.stress?.average, expected: 'number' }
  ];

  fields.forEach(field => {
    if (field.value != null && typeof field.value === field.expected) {
      log('pass', `${field.name}: ${field.value}`);
    } else if (field.value == null) {
      log('warn', `${field.name}: Not available`);
    } else {
      log('fail', `${field.name}: Invalid type (expected ${field.expected})`);
    }
  });

  // Test 6: Weekly trends
  console.log('\nTest 6: Weekly trends validation');
  const weeklyTrends = healthData.weeklyTrends || {};
  const trendFields = [
    'averageSleepScore',
    'averageEnergyScore',
    'averageSleepDuration',
    'averageRestingHR',
    'averageSteps'
  ];

  let trendsAvailable = 0;
  trendFields.forEach(field => {
    if (weeklyTrends[field] != null) {
      log('pass', `${field}: ${weeklyTrends[field]}`);
      trendsAvailable++;
    } else {
      log('warn', `${field}: Not available`);
    }
  });

  if (trendsAvailable > 0) {
    passed++;
  }

  // Summary
  console.log('\n' + '='.repeat(50));
  console.log('Test Summary');
  console.log('='.repeat(50));
  console.log(`${colors.green}Passed: ${passed}${colors.reset}`);
  if (failed > 0) {
    console.log(`${colors.red}Failed: ${failed}${colors.reset}`);
  }

  // Overall assessment
  console.log('\n' + '-'.repeat(50));
  if (freshnessResult.isFresh && validationResult.isValid) {
    log('pass', 'Health card should display correctly');
    console.log('');
    console.log('Data summary:');
    console.log(`  Last updated: ${new Date(healthData.lastUpdated).toLocaleString()}`);
    console.log(`  Age: ${freshnessResult.hoursSinceUpdate} hours`);
    console.log(`  Available metrics: ${validationResult.availableData.join(', ')}`);
  } else {
    log('warn', 'Health card may not display properly');
    if (!freshnessResult.isFresh) {
      console.log(`  - Data is too old (${freshnessResult.hoursSinceUpdate} hours)`);
    }
    if (!validationResult.isValid) {
      console.log('  - No valid health metrics found');
    }
  }
  console.log('');

  return failed === 0;
}

// Run tests
runTests().then(success => {
  process.exit(success ? 0 : 1);
});
