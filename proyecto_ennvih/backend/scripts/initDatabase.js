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

async function initDatabase() {
  console.log('🔧 Initializing database...');

  try {
    // Read and execute schema file
    const schemaPath = path.join(__dirname, '../bd/schema.sql');
    const schema = fs.readFileSync(schemaPath, 'utf8');

    console.log('📋 Creating tables...');
    await pool.query(schema);
    console.log('✅ Tables created successfully!');

    console.log('✨ Database initialization complete!');
  } catch (error) {
    console.error('❌ Error initializing database:', error.message);
    process.exit(1);
  } finally {
    await pool.end();
  }
}

initDatabase();
