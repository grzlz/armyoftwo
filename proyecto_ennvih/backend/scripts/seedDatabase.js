const { Pool } = require('pg');
const fs = require('fs');
const path = require('path');
require('dotenv').config();

const pool = new Pool({
  host: process.env.DB_HOST,
  port: process.env.DB_PORT,
  database: process.env.DB_NAME,
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
});

async function seedDatabase() {
  console.log('🌱 Seeding database...');

  try {
    // Read and execute seed data file
    const seedPath = path.join(__dirname, '../bd/seed_data.sql');
    const seedData = fs.readFileSync(seedPath, 'utf8');

    console.log('📊 Inserting seed data...');
    await pool.query(seedData);
    console.log('✅ Seed data inserted successfully!');

    // Verify data
    const result = await pool.query('SELECT COUNT(*) FROM languages');
    console.log(`📚 Total languages: ${result.rows[0].count}`);

    const coursesResult = await pool.query('SELECT COUNT(*) FROM courses');
    console.log(`📖 Total courses: ${coursesResult.rows[0].count}`);

    const vocabResult = await pool.query('SELECT COUNT(*) FROM vocabulary');
    console.log(`📝 Total vocabulary words: ${vocabResult.rows[0].count}`);

    console.log('✨ Database seeding complete!');
  } catch (error) {
    console.error('❌ Error seeding database:', error.message);
    process.exit(1);
  } finally {
    await pool.end();
  }
}

seedDatabase();
