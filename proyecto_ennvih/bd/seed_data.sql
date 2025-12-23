-- Seed Data for Indigenous Language Learning Platform
-- Initial data for Maya, Tzotzil, and Nahuatl

-- Insert Languages
INSERT INTO languages (name, code, native_name, description, total_speakers, flag_emoji) VALUES
('Spanish', 'es', 'Español', 'Base language for learning indigenous languages', 500000000, '🇲🇽'),
('English', 'en', 'English', 'Alternative base language', 1500000000, '🇺🇸'),
('Yucatec Maya', 'yua', 'Maaya t''aan', 'Mayan language spoken in Yucatán Peninsula', 800000, '🌿'),
('Tzotzil', 'tzo', 'Bats''i k''op', 'Mayan language spoken in Chiapas', 500000, '🏔️'),
('Nahuatl', 'nah', 'Nāhuatl', 'Uto-Aztecan language, language of the Aztecs', 1700000, '🦅');

-- Insert Courses
INSERT INTO courses (learning_language_id, from_language_id, title, description, level) VALUES
(3, 1, 'Spanish to Yucatec Maya', 'Learn Yucatec Maya from Spanish - Beginner Course', 'beginner'),
(4, 1, 'Spanish to Tzotzil', 'Learn Tzotzil from Spanish - Beginner Course', 'beginner'),
(5, 1, 'Spanish to Nahuatl', 'Learn Nahuatl from Spanish - Beginner Course', 'beginner'),
(3, 2, 'English to Yucatec Maya', 'Learn Yucatec Maya from English - Beginner Course', 'beginner'),
(4, 2, 'English to Tzotzil', 'Learn Tzotzil from English - Beginner Course', 'beginner'),
(5, 2, 'English to Nahuatl', 'Learn Nahuatl from English - Beginner Course', 'beginner');

-- Insert Skills for Spanish to Yucatec Maya Course
INSERT INTO skills (course_id, title, description, icon, order_index, xp_reward) VALUES
(1, 'Basics', 'Essential words and phrases', '👋', 1, 20),
(1, 'Greetings', 'Common greetings and introductions', '🤝', 2, 20),
(1, 'Family', 'Family members and relationships', '👨‍👩‍👧‍👦', 3, 20),
(1, 'Numbers', 'Counting from 1 to 20', '🔢', 4, 20),
(1, 'Food & Drink', 'Common foods and beverages', '🌮', 5, 20),
(1, 'Animals', 'Common animals in Maya culture', '🐆', 6, 20);

-- Insert Skills for Spanish to Tzotzil Course
INSERT INTO skills (course_id, title, description, icon, order_index, xp_reward) VALUES
(2, 'Basics', 'Essential words and phrases in Tzotzil', '👋', 1, 20),
(2, 'Greetings', 'Traditional Tzotzil greetings', '🤝', 2, 20),
(2, 'Family', 'Family terms in Tzotzil culture', '👨‍👩‍👧‍👦', 3, 20),
(2, 'Numbers', 'Tzotzil number system', '🔢', 4, 20),
(2, 'Nature', 'Words related to nature and mountains', '⛰️', 5, 20);

-- Insert Skills for Spanish to Nahuatl Course
INSERT INTO skills (course_id, title, description, icon, order_index, xp_reward) VALUES
(3, 'Basics', 'Essential words and phrases in Nahuatl', '👋', 1, 20),
(3, 'Greetings', 'Nahuatl greetings and courtesy', '🤝', 2, 20),
(3, 'Family', 'Family relationships in Nahuatl', '👨‍👩‍👧‍👦', 3, 20),
(3, 'Numbers', 'Aztec number system', '🔢', 4, 20),
(3, 'Food & Drink', 'Traditional Nahuatl food vocabulary', '🌽', 5, 20),
(3, 'Colors', 'Colors in Nahuatl', '🎨', 6, 20);

-- Insert Lessons for Yucatec Maya - Basics Skill
INSERT INTO lessons (skill_id, title, order_index, grammar_tips, xp_reward) VALUES
(1, 'Hello and Thank You', 1, 'Maya uses glottal stops (') which are important for pronunciation', 15),
(1, 'Common Phrases', 2, 'Word order in Maya can be different from Spanish', 15),
(1, 'Pronouns', 3, 'Maya has ergative-absolutive alignment in pronouns', 15);

-- Insert Lessons for Yucatec Maya - Greetings Skill
INSERT INTO lessons (skill_id, title, order_index, grammar_tips, xp_reward) VALUES
(2, 'Morning Greetings', 1, 'Time-based greetings are common in Maya culture', 15),
(2, 'Asking How Are You', 2, 'Learn to ask about wellbeing in Maya', 15),
(2, 'Introducing Yourself', 3, 'Formal and informal introductions', 15);

-- Insert Lessons for Tzotzil - Basics Skill
INSERT INTO lessons (skill_id, title, order_index, grammar_tips, xp_reward) VALUES
(7, 'Essential Words', 1, 'Tzotzil uses glottalized consonants', 15),
(7, 'Yes and No', 2, 'Affirmative and negative particles in Tzotzil', 15);

-- Insert Lessons for Nahuatl - Basics Skill
INSERT INTO lessons (skill_id, title, order_index, grammar_tips, xp_reward) VALUES
(13, 'Essential Words', 1, 'Nahuatl is an agglutinative language', 15),
(13, 'Pronunciation Guide', 2, 'Learn the unique sounds of Nahuatl including "tl"', 15);

-- Insert Vocabulary for Yucatec Maya
INSERT INTO vocabulary (language_id, word, translation, translation_language_id, pronunciation, part_of_speech, difficulty_level) VALUES
(3, 'Ba''ax ka wa''alik?', '¿Cómo estás?', 1, 'báash ka waʼáalik', 'phrase', 1),
(3, 'Ma''alob', 'Bien/Bueno', 1, 'máʼalob', 'adjective', 1),
(3, 'Dios bo''otik', 'Gracias', 1, 'dyos bóʼotik', 'phrase', 1),
(3, 'Túux ka táal?', '¿De dónde eres?', 1, 'túush ka táal', 'phrase', 1),
(3, 'In k''aaba''e...', 'Mi nombre es...', 1, 'in kʼáabaʼe', 'phrase', 1),
(3, 'Bix a beel?', '¿Cómo estás?', 1, 'bish a béel', 'phrase', 1),
(3, 'Janal', 'Comida', 1, 'hanal', 'noun', 1),
(3, 'Ha''', 'Agua', 1, 'haʼ', 'noun', 1),
(3, 'Noj', 'Grande', 1, 'noh', 'adjective', 1),
(3, 'Ch''ich''', 'Pájaro', 1, 'chʼichʼ', 'noun', 1);

-- Insert Vocabulary for Tzotzil
INSERT INTO vocabulary (language_id, word, translation, translation_language_id, pronunciation, part_of_speech, difficulty_level) VALUES
(4, 'K''usi chaval?', '¿Cómo estás?', 1, 'kʼusi chaval', 'phrase', 1),
(4, 'Lek', 'Bien', 1, 'lek', 'adjective', 1),
(4, 'Kolavalex', 'Gracias', 1, 'kolavalex', 'phrase', 1),
(4, 'Buch''u avich''', '¿Cómo te llamas?', 1, 'buchʼu avichʼ', 'phrase', 1),
(4, 'We''el', 'Comida', 1, 'weʼel', 'noun', 1),
(4, 'Vo''', 'Agua', 1, 'voʼ', 'noun', 1),
(4, 'Muk''', 'Grande', 1, 'mukʼ', 'adjective', 1),
(4, 'Mut', 'Pájaro', 1, 'mut', 'noun', 1),
(4, 'Vokol', 'Maíz', 1, 'vokol', 'noun', 1),
(4, 'Jol', 'Cabeza', 1, 'hol', 'noun', 1);

-- Insert Vocabulary for Nahuatl
INSERT INTO vocabulary (language_id, word, translation, translation_language_id, pronunciation, part_of_speech, difficulty_level) VALUES
(5, 'Niltze', 'Hola', 1, 'niltse', 'interjection', 1),
(5, 'Tlazohcamati', 'Gracias', 1, 'tlasohkamati', 'phrase', 1),
(5, '¿Quen otinemi?', '¿Cómo estás?', 1, 'ken otinemi', 'phrase', 1),
(5, 'Cualli', 'Bien/Bueno', 1, 'kwalli', 'adjective', 1),
(5, 'Notoka...', 'Mi nombre es...', 1, 'notoka', 'phrase', 1),
(5, 'Tlacatl', 'Hombre/Persona', 1, 'tlakatl', 'noun', 1),
(5, 'Cihuatl', 'Mujer', 1, 'siwaːtl', 'noun', 1),
(5, 'Atl', 'Agua', 1, 'atl', 'noun', 1),
(5, 'Tlaxcalli', 'Tortilla', 1, 'tlashkalli', 'noun', 1),
(5, 'Xochitl', 'Flor', 1, 'shochitl', 'noun', 1),
(5, 'Calli', 'Casa', 1, 'kalli', 'noun', 1),
(5, 'Tonatiuh', 'Sol', 1, 'tonatiwh', 'noun', 1);

-- Insert Exercises for Maya Lesson 1
INSERT INTO exercises (lesson_id, type, order_index, question, correct_answer, xp_reward) VALUES
(1, 'translation', 1, 'Translate to Maya: Gracias', 'Dios bo''otik', 5),
(1, 'multiple_choice', 2, 'How do you say "Good" in Maya?', 'Ma''alob', 5),
(1, 'translation', 3, 'Translate to Spanish: Bix a beel?', '¿Cómo estás?', 5);

-- Insert Multiple Choice Options for Maya Exercise 2
INSERT INTO exercise_options (exercise_id, option_text, is_correct, order_index) VALUES
(2, 'Ma''alob', true, 1),
(2, 'Janal', false, 2),
(2, 'Ha''', false, 3),
(2, 'Noj', false, 4);

-- Insert Exercises for Tzotzil
INSERT INTO exercises (lesson_id, type, order_index, question, correct_answer, xp_reward) VALUES
(4, 'translation', 1, 'Translate to Tzotzil: Gracias', 'Kolavalex', 5),
(4, 'multiple_choice', 2, 'How do you say "Good" in Tzotzil?', 'Lek', 5);

-- Insert Multiple Choice Options for Tzotzil Exercise
INSERT INTO exercise_options (exercise_id, option_text, is_correct, order_index) VALUES
(5, 'Lek', true, 1),
(5, 'Mut', false, 2),
(5, 'Vo''', false, 3),
(5, 'We''el', false, 4);

-- Insert Exercises for Nahuatl
INSERT INTO exercises (lesson_id, type, order_index, question, correct_answer, xp_reward) VALUES
(6, 'translation', 1, 'Translate to Nahuatl: Hola', 'Niltze', 5),
(6, 'multiple_choice', 2, 'How do you say "Thank you" in Nahuatl?', 'Tlazohcamati', 5),
(6, 'translation', 3, 'Translate to Spanish: Cualli', 'Bien', 5);

-- Insert Multiple Choice Options for Nahuatl Exercise
INSERT INTO exercise_options (exercise_id, option_text, is_correct, order_index) VALUES
(7, 'Tlazohcamati', true, 1),
(7, 'Niltze', false, 2),
(7, 'Atl', false, 3),
(7, 'Cualli', false, 4);

-- Insert Achievements
INSERT INTO achievements (name, description, icon, requirement_type, requirement_value) VALUES
('First Steps', 'Complete your first lesson', '🎯', 'lessons_completed', 1),
('Dedicated Learner', 'Maintain a 7-day streak', '🔥', 'streak', 7),
('Polyglot', 'Learn all three indigenous languages', '🌍', 'courses_enrolled', 3),
('XP Master', 'Earn 1000 XP total', '⭐', 'total_xp', 1000),
('Cultural Explorer', 'Read 10 cultural notes', '📚', 'cultural_notes_read', 10),
('Centenario', 'Complete 100 lessons', '💯', 'lessons_completed', 100);

-- Insert Cultural Notes
INSERT INTO cultural_notes (language_id, skill_id, title, content) VALUES
(3, 1, 'The Maya Writing System', 'The ancient Maya developed one of the most sophisticated writing systems in pre-Columbian Americas. While Yucatec Maya today uses the Latin alphabet, the traditional hieroglyphic script was used for over a thousand years.'),
(3, 2, 'Maya Greetings and Respect', 'In Maya culture, greetings often include asking about one''s wellbeing and family. Elders are greeted with special respect, and it''s customary to use formal language when addressing them.'),
(4, 1, 'Tzotzil Communities in Chiapas', 'Tzotzil is primarily spoken in the highlands of Chiapas. The Tzotzil people maintain strong cultural traditions, including distinctive textiles and spiritual practices that blend indigenous and Catholic elements.'),
(5, 1, 'Nahuatl: Language of the Aztecs', 'Nahuatl was the language of the Aztec Empire. Many words we use today come from Nahuatl: chocolate (xocolatl), tomato (tomatl), avocado (ahuacatl), and coyote (coyotl).'),
(5, 5, 'Sacred Foods in Nahuatl Culture', 'Maize (corn) was sacred to the Nahua people. According to their creation story, humans were made from corn. The word tlaxcalli (tortilla) remains central to Mexican cuisine today.');

-- Link vocabulary to lessons
INSERT INTO lesson_vocabulary (lesson_id, vocabulary_id) VALUES
(1, 1), (1, 2), (1, 3), -- Maya Lesson 1
(2, 4), (2, 5), (2, 6), -- Maya Lesson 2
(4, 11), (4, 12), (4, 13), -- Tzotzil Lesson 1
(6, 21), (6, 22), (6, 23); -- Nahuatl Lesson 1
