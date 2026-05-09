exports.up = async (db) => {
  await db.createTable('users', {
    id: 'uuid',
    email: 'string',
    created_at: 'timestamp'
  });
};

exports.down = async (db) => {
  await db.dropTable('users');
};
